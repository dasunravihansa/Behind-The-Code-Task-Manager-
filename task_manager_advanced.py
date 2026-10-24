"""Behind The Code — Learn Python the Smart Way, Part 2.

Python 3.9+. Standard library only. Run this file in Pydroid 3 or Python.
Keep the script in a writable folder. One running instance at a time.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Callable, TypedDict

FILE = Path(__file__).resolve().with_name("tasks.json")


class Task(TypedDict):
    id: int
    title: str
    completed: bool


def validate_tasks(data: object) -> list[Task]:
    if not isinstance(data, list):
        raise ValueError("Saved data must be a list.")
    seen: set[int] = set()
    clean: list[Task] = []
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("Every task must be an object.")
        task_id = item.get("id")
        title = item.get("title")
        completed = item.get("completed")
        if type(task_id) is not int or task_id < 1 or task_id in seen:
            raise ValueError("Task IDs must be unique positive integers.")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Every task needs a non-empty title.")
        if type(completed) is not bool:
            raise ValueError("Completion status must be a boolean.")
        seen.add(task_id)
        clean.append({"id": task_id, "title": title.strip(), "completed": completed})
    return clean


def load_tasks(path: Path = FILE) -> list[Task]:
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    return validate_tasks(data)


def save_tasks(tasks: list[Task], path: Path = FILE) -> None:
    """Write a complete temporary file before replacing the previous save.

    This reduces partial-file risk. It is not a backup, a concurrency lock,
    or a guarantee against every power-loss scenario.
    """
    clean = validate_tasks(tasks)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=path.name + ".", suffix=".tmp", delete=False
        ) as file:
            temporary = Path(file.name)
            json.dump(clean, file, indent=2, ensure_ascii=False)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def add_task(tasks: list[Task], title: str) -> list[Task]:
    title = title.strip()
    if not title:
        raise ValueError("Task title cannot be empty.")
    # Unique among current tasks; a removed highest ID may be reused.
    next_id = max((task["id"] for task in tasks), default=0) + 1
    task: Task = {"id": next_id, "title": title, "completed": False}
    return [*tasks, task]


def find_task(tasks: list[Task], task_id: int) -> Task:
    task = next((task for task in tasks if task["id"] == task_id), None)
    if task is None:
        raise ValueError("Task not found.")
    return task


def complete_task(tasks: list[Task], task_id: int) -> list[Task]:
    find_task(tasks, task_id)
    return [
        {**task, "completed": True} if task["id"] == task_id else task
        for task in tasks
    ]


def delete_task(tasks: list[Task], task_id: int) -> list[Task]:
    find_task(tasks, task_id)
    return [task for task in tasks if task["id"] != task_id]


def pending_titles(tasks: list[Task]) -> list[str]:
    return [task["title"] for task in tasks if not task["completed"]]


def view_tasks(tasks: list[Task]) -> list[Task]:
    if not tasks:
        print("No tasks found.")
    for task in tasks:
        status = "Done" if task["completed"] else "Pending"
        print(f'{task["id"]}. {task["title"]} [{status}]')
    return tasks


def read_id() -> int:
    value = int(input("Task ID: "))
    if value < 1:
        raise ValueError("Task ID must be positive.")
    return value


def handle_add(tasks: list[Task]) -> list[Task]:
    return add_task(tasks, input("Task title: "))


def handle_complete(tasks: list[Task]) -> list[Task]:
    return complete_task(tasks, read_id())


def handle_delete(tasks: list[Task]) -> list[Task]:
    return delete_task(tasks, read_id())


def main() -> None:
    try:
        tasks = load_tasks()
    except (OSError, ValueError) as error:
        print(f"Cannot load tasks: {error}")
        print("The existing file was left unchanged. Fix or back it up first.")
        return

    actions: dict[str, Callable[[list[Task]], list[Task]]] = {
        "1": handle_add,
        "2": view_tasks,
        "3": handle_complete,
        "4": handle_delete,
    }
    while True:
        print("\n=== PYTHON TASK MANAGER ===")
        print("1. Add Task\n2. View Tasks\n3. Complete Task\n4. Delete Task\n5. Exit")
        choice = input("Choose: ").strip()
        if choice == "5":
            print("Goodbye!")
            break
        action = actions.get(choice)
        if action is None:
            print("Invalid option.")
            continue
        try:
            candidate = action(tasks)
            if candidate is not tasks:
                save_tasks(candidate)
                tasks = candidate
                print("Changes saved!")
        except ValueError as error:
            print(f"Invalid input: {error}")
        except OSError as error:
            print(f"Save failed: {error}. Changes were not applied.")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye!")
