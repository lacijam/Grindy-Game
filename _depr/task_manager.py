from dataclasses import dataclass, field

@dataclass
class Task:
    id: str
    name: str
    type: str
    target: str = ""
    count: int = 0
    requirements: dict = field(default_factory=dict)
    rewards: dict = field(default_factory=dict)
    completed: bool = False
    ready_to_claim: bool = False
    progress: int = 0
    difficulty: str = ""

class TaskManager:
    def __init__(self, player, message_log, sound_manager):
        self.player = player
        self.message_log = message_log
        self.sound_manager = sound_manager
        self.tasks = self._load_tasks()
        self.completed_task_ids = set()

    def _load_tasks(self):
        from task_data import TASK_DATA
        tasks = []

        for task_template in TASK_DATA:
            task = Task(
                id=task_template["id"],
                name=task_template["name"],
                type=task_template["task"]["type"],
                target=task_template["task"].get("target", ""),
                count=task_template["task"].get("count", 0),
                requirements=task_template.get("requirements", {}),
                rewards=task_template.get("rewards", {}),
                difficulty=task_template.get("difficulty", ""),
            )
            tasks.append(task)

        return tasks

    def handle_kill(self, enemy_id):
        for task in self.tasks:
            if task.completed:
                continue
            if task.type != "kill" or task.target != enemy_id:
                continue

            task.progress += 1
            self._check_completion(task)


    def handle_resource_gain(self, resource_id, amount=1):
        for task in self.tasks:
            if task.completed:
                continue
            if task.type != "gain" or task.target != resource_id:
                continue

            task.progress += amount
            self._check_completion(task)

    def handle_node_gather(self, node_id, amount=1):
        for task in self.tasks:
            if task.completed:
                continue
            if task.type != "gather" or task.target != node_id:
                continue

            task.progress += amount
            self._check_completion(task)

    def handle_level_up(self, skill, new_level):
        for task in self.tasks:
            if task.completed:
                continue
            if task.type != "reach_level" or task.target != skill:
                continue

            task.progress = new_level

            if new_level < task.count or task.ready_to_claim:
                continue

            task.ready_to_claim = True
            self._log_task_ready_to_claim_message(task)

    def handle_craft(self, item_id, amount=1):
        for task in self.tasks:
            if task.completed:
                continue
            if task.type != "craft" or task.target != item_id:
                continue

            task.progress += amount
            self._check_completion(task)

    def _check_completion(self, task):
        if task.progress < task.count:
            return
        if task.ready_to_claim or task.completed:
            return

        task.ready_to_claim = True
        self._log_task_ready_to_claim_message(task)

    def claim_task(self, task_id):
        for task in self.tasks:
            if task.id != task_id or not task.ready_to_claim or task.completed:
                continue

            self._grant_rewards(task)

            task.completed = True
            task.ready_to_claim = False
            self.completed_task_ids.add(task.id)

            reward_strings = self._format_rewards(task.rewards)
            reward_text = ", ".join(reward_strings) if reward_strings else "No Rewards"

            self.message_log.queue([
                (f"{task.name}: ", (100, 255, 100)),
                (reward_text, (100, 255, 100)),
                (" claimed", "white"),
            ])

            self.sound_manager.queue("task_claim")

    def _grant_rewards(self, task):
        rewards = task.rewards
        log_cb = None  # optional callback if you want message log

        if "item" in rewards:
            self.player.inventory.add_item(rewards["item"], rewards.get("qty", 1), log_cb)
        if "coins" in rewards:
            self.player.gold += rewards["coins"]

        self.completed_task_ids.add(task.id)

    def _log_task_ready_to_claim_message(self, task):
        self.message_log.queue([
            ("Task Completed: ", (255, 255, 0)),
            (task.name, (255, 255, 0)),
        ])

        self.sound_manager.queue("task_ready")

    def get_task_category(self, task):
        if task.completed:
            return "completed"
        if task.ready_to_claim:
            return "available"

        for skill, required_level in task.requirements.items():
            if self.player.skills.get_skill_level(skill) < required_level:
                return "unavailable"

        return "available"

    def get_tasks_by_category(self):
        categories = {"available": [], "unavailable": [], "completed": []}

        for task in self.tasks:
            cat = self.get_task_category(task)
            categories[cat].append(task)

        return categories

    def _format_rewards(self, rewards):
        reward_strings = []

        for k, v in rewards.items():
            if k == "item":
                reward_strings.append(f"{v.title()} x{rewards.get('qty',1)}")
            elif k == "coins":
                reward_strings.append(f"{v} Coins")

        return reward_strings
