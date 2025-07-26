from state import State

class StateMachine:
    def __init__(self):
        self.states = {}
        self.current_state = None
        self.timer = 0

    def add_state(self, state: State):
        self.states[state.name] = state

    def change_state(self, name, entity, ctx):
        if self.current_state:
            self.current_state.exit(entity, ctx)
        self.current_state = self.states.get(name)
        if self.current_state:
            self.current_state.enter(entity, ctx)

    def update(self, entity, dt, ctx):
        self.timer -= dt
        if self.current_state:
            self.current_state.update(entity, dt, ctx)