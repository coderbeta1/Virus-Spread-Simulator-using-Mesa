from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
# from batchrunner import BatchRunner

# Define the person stats
class PersonAgent(Agent):
    '''We shall assume the person is called bob'''
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.infection_status = initial_health_status  # 0: "susceptible" 1: "infected" 2: "recovered"
        self.infection_probability = infection_probability  # Probability of getting infected
        self.recovery_time = recovery_time  # Time it takes to recover
        self.days_infected = 0  # Time for which the agent is infected
        self.location = None    # Current Location of bob
        self.age = 10   # bob's Age
        self.behavior = initial_behavior # bob's behaviorial traits
        self.culture = initial_culture  # bob's culture
        self.income = 10    # bob's income
        self.social_contacts = set()    # bob's contacts
        self.hygiene = initial_hygiene  # bob's hygiene following
        self.mask_wearing_probability = 0.0  # Probability of wearing a mask
        self.social_distancing_compliance = 0.0  # Probability of social distancing
        self.vaccinated = False # Vaccination Status

    def step(self):
        if self.health_status == "infected":
            self.days_infected += 1
            if self.days_infected >= self.recovery_time:
                self.health_status = "recovered"
        elif self.health_status == "susceptible":
            self.try_to_infect()

        # Implement agent movement, interactions, and other behaviors
        self.move()
        self.interact()

    def move(self):
        # Implement agent movement logic here
        pass

    def interact(self):
        # Implement agent interactions here, considering social contacts and infection spread
        pass

    def try_to_infect(self):
        # Implement logic to attempt to infect susceptible agents based on interactions and infection_probability
        pass

# Define the main model
class VirusSpreadModel(Model):
    def __init__(self, width, height, N, initial_infection_pct, recovery_time):
        self.num_agents = N
        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)

        # Create agents and infect a portion of them initially
        for i in range(self.num_agents):
            if i < initial_infection_pct * self.num_agents:
                agent = PersonAgent(i, self, "infected", infection_probability, recovery_time)
            else:
                agent = PersonAgent(i, self, "susceptible", infection_probability, recovery_time)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(agent, (x, y))
            self.schedule.add(agent)

    def step(self):
        self.schedule.step()
