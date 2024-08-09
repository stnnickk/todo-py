import wx
import json
import os
import uuid
from functools import partial
import moment


# Основной класс окна приложения
class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        super().__init__(parent, title=title)

        # Загрузка задач из файла и инициализация списка идентификаторов задач
        self.tasks = self.loadTasks()
        self.taskIds = []

        # Создание панели для размещения элементов интерфейса
        self.panel = wx.Panel(self)

        # Горизонтальный сSizer для заголовка и количества задач
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        # Создание и добавление статических текстовых элементов
        self.text = wx.StaticText(self.panel, label="Tasks")
        self.text2 = wx.StaticText(self.panel, label=str(len(self.tasks)))

        hbox.Add(self.text, flag=wx.ALIGN_LEFT | wx.ALL, border=10)
        hbox.AddStretchSpacer()
        hbox.Add(self.text2, flag=wx.ALIGN_LEFT | wx.ALL, border=10)

        # Кнопка для создания новой задачи
        self.createBtn = wx.Button(self.panel, label="Create task", size=(100, 30))
        self.createBtn.Bind(wx.EVT_BUTTON, self.openTaskWindow)

        # Вертикальный сSizer для размещения горизонтального сSizer и кнопки
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(hbox, flag=wx.EXPAND)
        vbox.Add(self.createBtn, flag=wx.EXPAND | wx.ALL, border=10)

        # Панель и сSizer для списка задач
        self.taskPanel = wx.Panel(self.panel)
        self.taskVbox = wx.BoxSizer(wx.VERTICAL)
        self.taskPanel.SetSizer(self.taskVbox)

        # Список с флажками для отображения задач
        self.checkList = wx.CheckListBox(self.taskPanel, choices=[])
        self.checkList.Bind(wx.EVT_CONTEXT_MENU, self.onTaskContextMenu)
        self.checkList.Bind(wx.EVT_CHECKLISTBOX, self.onMakeDone)
        self.checkList.Bind(wx.EVT_LISTBOX_DCLICK, self.onTaskDoubleClick)
        self.taskVbox.Add(
            self.checkList, proportion=1, flag=wx.EXPAND | wx.ALL, border=10
        )

        # Добавление панели со списком задач в вертикальный сSizer
        vbox.Add(self.taskPanel, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)

        # Отображение списка задач
        self.updateTaskList()

        # Установка сSizer для основной панели
        self.panel.SetSizer(vbox)

    def openTaskWindow(self, event):
        new_window = CreateTaskWindow(self, "Create task")
        new_window.Show()

    def updateTaskList(self):
        # Преобразование строки обратно в moment для сортировки
        for task in self.tasks:
            task["dateAdded"] = moment.date(task["dateAdded"])

        # Сортировка задач по дате добавления в порядке убывания
        self.tasks.sort(key=lambda task: task["dateAdded"], reverse=True)
        self.checkList.Clear()
        self.taskIds.clear()

        for i, task in enumerate(self.tasks):
            # Определение текста для отображения задачи
            taskTitle = task["title"]
            if task.get("isDone", False):
                taskTitle += " (completed)"

            # Добавление задачи в список и сохранение идентификатора
            self.checkList.Append(taskTitle)
            self.taskIds.append(task["id"])

            # Установка флажка, если задача выполнена
            if task.get("isDone", False):
                self.checkList.Check(i)

    def addTask(self, title, description):
        # Создание новой задачи
        task = {
            "id": str(uuid.uuid4()),  # Генерация уникального идентификатора задачи
            "title": title,
            "description": description,
            "isDone": False,
            "dateAdded": moment.now().format("YYYY-MM-DDTHH:mm:ss"),
        }
        # Добавление задачи в список и обновление файла
        self.tasks.append(task)
        self.taskIds.append(task["id"])
        self.updateJsonFile()

        # Обновление списка задач и панели
        self.checkList.Append(title)
        self.text2.SetLabel(str(len(self.tasks)))

        self.updateTaskList()
        self.taskPanel.Layout()
        self.panel.Update()

        print(self.tasks)

    def onTaskContextMenu(self, event):
        selectedIndex = self.checkList.GetSelection()

        if selectedIndex != wx.NOT_FOUND:
            taskMenu = wx.Menu()
            editTask = wx.MenuItem(taskMenu, wx.ID_EDIT, "Edit Task")
            deleteTask = wx.MenuItem(taskMenu, wx.ID_DELETE, "Delete Task")

            taskMenu.Append(editTask)
            taskMenu.Append(deleteTask)

            taskId = self.taskIds[selectedIndex]

            self.Bind(wx.EVT_MENU, partial(self.onEditTask, taskId), editTask)
            self.Bind(wx.EVT_MENU, partial(self.onDeleteTask, taskId), deleteTask)

            self.PopupMenu(taskMenu)
            taskMenu.Destroy()

    def onDeleteTask(self, id, event):
        self.tasks = [task for task in self.tasks if task["id"] != id]
        self.updateTaskList()
        self.updateJsonFile()
        self.text2.SetLabel(str(len(self.tasks)))
        wx.MessageBox("Task deleted.", "Delete Task", wx.OK | wx.ICON_INFORMATION)

    def onEditTask(self, id, event):
        new_window = EditTaskWindow(self, "Edit task", self.checkList.GetSelection())
        new_window.Show()

    def updateJsonFile(self):
        filePath = os.path.abspath("tasks.json")
        with open(filePath, "w") as file:
            # Преобразование объектов moment в строки
            tasksToSave = [
                {
                    **task,
                    "dateAdded": moment.date(task["dateAdded"]).format(
                        "YYYY-MM-DDTHH:mm:ss"
                    ),  # Преобразование в строку
                }
                for task in self.tasks
            ]
            json.dump(tasksToSave, file)

    def onTaskDoubleClick(self, event):
        selectedIndex = self.checkList.GetSelection()

        if selectedIndex != wx.NOT_FOUND:
            task_id = self.taskIds[selectedIndex]
            task = next(task for task in self.tasks if task["id"] == task_id)

            created_date = task["dateAdded"].format("YYYY-MM-DD")
            created_time = task["dateAdded"].format("HH:mm:ss")

            wx.MessageBox(
                f"Task details:\n\nTitle: {task['title']}\nDescription: {task['description']}\nCreated: {created_date} at {created_time}",
                "Task Details",
                wx.OK | wx.ICON_INFORMATION,
            )

    def onMakeDone(self, event):
        selectedIndex = event.GetSelection()

        if selectedIndex != wx.NOT_FOUND:
            task_id = self.taskIds[selectedIndex]
            task = next(task for task in self.tasks if task["id"] == task_id)

            isChecked = self.checkList.IsChecked(selectedIndex)
            task["isDone"] = isChecked

            self.updateTaskList()
            self.updateJsonFile()

    def loadTasks(self):
        # Загрузка задач из файла
        try:
            with open("tasks.json", "r") as file:
                tasks = json.load(file)

                # Преобразование строковых дат обратно в объекты moment
                for task in tasks:
                    task["dateAdded"] = moment.date(task["dateAdded"])

                return tasks
        except (FileNotFoundError, json.JSONDecodeError):
            return []


# Класс для создания новой задачи
class CreateTaskWindow(wx.Frame):
    def __init__(self, parent, title):
        super().__init__(parent, title=title, size=(400, 400))
        self.parent = parent

        panel = wx.Panel(self)

        # Вертикальный сSizer для размещения элементов
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        mainSizer.Add(hbox, flag=wx.EXPAND)

        # Элементы ввода для создания задачи
        self.label = wx.StaticText(panel, label="Title:")
        self.title_ctrl = wx.TextCtrl(panel)
        self.label2 = wx.StaticText(panel, label="Description:")
        self.text_field = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        self.createTaskBtn = wx.Button(panel, label="Create task")
        self.createTaskBtn.Bind(wx.EVT_BUTTON, self.onCreateTask)

        hbox.Add(self.label, flag=wx.ALL, border=10)
        hbox.Add(self.title_ctrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)

        mainSizer.Add(self.label2, flag=wx.ALL, border=10)
        mainSizer.Add(self.text_field, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        mainSizer.Add(self.createTaskBtn, flag=wx.ALIGN_RIGHT | wx.ALL, border=10)

        panel.SetSizer(mainSizer)

    def onCreateTask(self, event):
        taskTitle = self.title_ctrl.GetValue()
        taskDesc = self.text_field.GetValue()

        if taskTitle == "" or taskDesc == "":
            self.onShowMessage(event)
        else:
            self.parent.addTask(taskTitle, taskDesc)
            self.title_ctrl.Clear()
            self.text_field.Clear()

    def onShowMessage(self, event):
        dlg = wx.MessageDialog(self, "Enter data", "Error", wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()


# Класс для редактирования существующей задачи
class EditTaskWindow(wx.Frame):
    def __init__(self, parent, title, selectionIndex):
        super().__init__(parent, title=title, size=(400, 400))

        # Сохранение ссылок на родительский объект и методы обновления
        self.parent = parent
        self.taskIds = parent.taskIds
        self.tasks = parent.tasks
        self.updateTaskList = parent.updateTaskList
        self.updateJsonFile = parent.updateJsonFile

        panel = wx.Panel(self)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        mainSizer.Add(hbox, flag=wx.EXPAND)

        # Поиск задачи для редактирования
        taskId = self.taskIds[selectionIndex]
        self.task = next(task for task in self.tasks if task["id"] == taskId)

        # Элементы для редактирования задачи
        self.label = wx.StaticText(panel, label="Title:")
        self.title_ctrl = wx.TextCtrl(panel, value=self.task["title"])
        self.label2 = wx.StaticText(panel, label="Description:")
        self.text_field = wx.TextCtrl(
            panel, style=wx.TE_MULTILINE, value=self.task["description"]
        )
        self.changeTaskBtn = wx.Button(panel, label="Change")
        self.changeTaskBtn.Bind(wx.EVT_BUTTON, self.onChangeTask)

        # Размещение элементов в интерфейсе
        hbox.Add(self.label, flag=wx.ALL, border=10)
        hbox.Add(self.title_ctrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        mainSizer.Add(self.label2, flag=wx.ALL, border=10)
        mainSizer.Add(self.text_field, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        mainSizer.Add(self.changeTaskBtn, flag=wx.ALIGN_RIGHT | wx.ALL, border=10)

        panel.SetSizer(mainSizer)

    def onChangeTask(self, event):
        newTitle = self.title_ctrl.GetValue()
        newDesc = self.text_field.GetValue()

        if newTitle == "" or newDesc == "":
            self.onShowMessage(event, "Title and description cannot be empty.")
        elif newTitle == self.task["title"] and newDesc == self.task["description"]:
            self.onShowMessage(event, "No changes made.")
        else:
            self.task["title"] = newTitle
            self.task["description"] = newDesc

            self.updateTaskList()
            self.updateJsonFile()

    def onShowMessage(self, event, message):
        dlg = wx.MessageDialog(self, message, "Error", wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()


app = wx.App()
frame = MyFrame(None, "ToDo App")
frame.Centre()
frame.Show()

app.MainLoop()
