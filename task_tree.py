import uuid
import json
import os

class Task:
    def __init__(self, name, id=None, parent_id=None):
        self.id = id if id is not None else str(uuid.uuid4())  # Use provided ID or generate a new one
        self.name = name
        self.parent_id = parent_id  # Parent node ID
        self.children = []  # List of child nodes

    def to_dict(self):
        """将任务节点转为字典格式，便于保存到 JSON 文件。"""
        return {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id,
            "children": [child.to_dict() for child in self.children]
        }
    def print(self, level=0):
        """递归打印任务树，用于调试输出。"""
        indent = "    " * int(level)
        print(f"{indent}- {self.name} (ID: {self.id})")
        for child in self.children:
            child.print(level + 1) 

class TaskTree:
    def __init__(self, filename="task_tree.json"):
        self.filename = filename
        self.root = Task("Root")  # 根节点
        self.current_task = self.root
        self.load_from_file()

    def add_task(self, name):
        new_task = Task(name, parent_id=self.current_task.id)
        self.current_task.children.append(new_task)
        self.current_task = new_task
        self.save_to_file()
        
    def rename_task(self, new_name):
        """Rename the current task, ensuring the root node's name is immutable."""
        if self.current_task == self.root:
            print("根节点名称不可修改。")
            return
        self.current_task.name = new_name
        self.save_to_file()
        
    def load_from_file(self):
        """从 JSON 文件加载任务树，并设置当前专注任务。如果文件不存在，则创建一个新文件并初始化任务树。"""
        if not os.path.exists(self.filename):
            print(f"{self.filename} 不存在，正在创建新文件并初始化任务树。")
            self.save_to_file()
        else:
            try:
                with open(self.filename, 'r') as file:
                    data = json.load(file)
                    # 验证文件格式
                    if not self.validate_data_format(data):
                        self.handle_file_format_error()
                        return
                    
                    # 从文件加载任务树和当前任务
                    self.root = self.dict_to_task(data["root"])
                    self.current_task_id = data.get("current_task_id")
                    self.current_task = self.find_task_by_id(self.root, self.current_task_id)
                    print(f"成功从 {self.filename} 加载任务树，当前专注任务为：{self.current_task.name}")
            except (json.JSONDecodeError, KeyError) as e:
                # 捕获 JSON 解析错误或关键数据缺失情况
                print(f"文件读取失败，原因：{e}")
                self.handle_file_format_error()
                
                
    def save_to_file(self, filename=None):
        """将任务树保存到 JSON 文件，并记录当前专注任务的 id���"""
        if filename == None:
            filename = self.filename
        with open(filename, 'w') as file:
            data = {
                "root": self.task_to_dict(self.root),
                "current_task_id": self.current_task.id  # 记录当前专注任务的 id
            }
            json.dump(data, file, indent=4)

    def validate_data_format(self, data):
        """验证 JSON 数据的格式是否符合预期。"""
        # 检查数据中是否包含 "root" 和 "current_task_id" 字段
        if "root" not in data or "current_task_id" not in data:
            return False
        # 检查 root 是否具有符合任务格式的基本字段
        return isinstance(data["root"], dict) and "name" in data["root"] and "children" in data["root"]

    def handle_file_format_error(self):
        """处理文件格式错误的情况，提供选项重新创建或检查文件。"""
        print("任务文件格式不符合预期。请确认文件结构或选择以下选项：")
        try:
            choice = input("输入 '1' 重新创建文件，输入 '2' 检查文件并重新加载：").strip()
        except EOFError:
            choice = ""  # 处理无法输入的情况

        if choice == '1':
            self.root = Task("Root")  # 重新初始化根节点
            self.current_task = self.root
            self.save_to_file()
            print(f"已重新创建 {self.filename} 文件。")
        elif choice == '2':
            print("请手动检查文件内容，并确保格式正确。")
        else:
            print("未选择有效选项，默认重新创建文件。")
            self.root = Task("Root")  # 默认重新初始化
            self.current_task = self.root
            self.save_to_file()

    def task_to_dict(self, task):
        """将任务转换为字典格式，用于保存到 JSON 文件。"""
        return {
            "id": task.id,
            "name": task.name,
            "children": [self.task_to_dict(child) for child in task.children]
        }

    def dict_to_task(self, data):
        """从字典格式的数据重建任务树。"""
        task = Task(data["name"], data["id"], data.get("parent_id"))
        task.children = [self.dict_to_task(child) for child in data["children"]]
        return task

    def find_task_by_id(self, task, task_id):
        """根据 id 查找任务。"""
        if task.id == task_id:
            return task
        for child in task.children:
            result = self.find_task_by_id(child, task_id)
            if result:
                return result
        return None

    def complete_task(self):
        """完成当前任务，将专注任务指针退回到父节点。"""
        if self.current_task == self.root:
            print("根节点不可完成。")
            return
        parent_task = self.find_parent(self.root, self.current_task)
        if parent_task:
            self.current_task = parent_task
            print(f"已完成任务，回退到父任务：{self.current_task.name}")
            self.save_to_file()

    def find_parent(self, parent, child):
        """找到指定任务的父任务。"""
        for node in parent.children:
            if node == child:
                return parent
            result = self.find_parent(node, child)
            if result:
                return result
        return None



if __name__ == "__main__":
    task_tree = TaskTree()
    task_tree.save_to_file(filename="task_tree_start.json")
    task_tree.rename_task("subtask 1.1 renamed")
    task_tree.complete_task()

    
    # 保存并查看 JSON 格式的任务树
    task_tree.save_to_file()
    print("任务树已保存为 JSON 文件。")
