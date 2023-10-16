# Import necessary Mesa modules
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import ContinuousSpace
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
# from mesa.space import ContinuousSpace
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import ChartModule
from mesa.visualization.UserParam import (NumberInput, Slider)

import random
import numpy
import numpy.random

import economyModel

# Statistics Calculation
def compute_susceptible_count(model):
    susceptible_count = 0
    for agent in model.schedule.agents:
        if (agent.infection_status == "susceptible"):
            susceptible_count+=1
    return susceptible_count
def compute_infected_count(model):
    susceptible_count = 0
    for agent in model.schedule.agents:
        if (agent.infection_status == "infected"):
            susceptible_count+=1
    return susceptible_count
def compute_immune_count(model):
    susceptible_count = 0
    for agent in model.schedule.agents:
        if (agent.infection_status == "immune"):
            susceptible_count+=1
    return susceptible_count
def compute_public_distress(model):
    for agent in model.schedule.agents:
        pass
    return

# Define the main model
class VirusSpreadModel(Model):
    def __init__(self, width, height, population_size, intitial_infected_percent,
    initial_immune_percent, hospital_limit, prob_spread, dist_spread, total_economy,
    minimum_income, minimum_expense, amplitudes):
        self.population_size = population_size
        self.width = width
        self.height = height
        self.grid = MultiGrid(width, height, torus=True)
        self.schedule = RandomActivation(self)
        self.initial_infected_percent = intitial_infected_percent
        self.initial_immune_percent = initial_immune_percent
        self.hospital_limit = hospital_limit
        self.prob_spread = prob_spread
        self.dist_spread = dist_spread
        self.total_economy = total_economy
        self.minimum_income = minimum_income
        self.minimum_expense = minimum_expense
        self.amplitudes = amplitudes

        # Add Function Randomisers
        social_stratum_randomised = numpy.random.rand(population_size) * 100 // 20
        age_randomised = numpy.random.beta(2, 6, population_size) * 100

        infection_probability_randomised = numpy.random.normal(0.5, 0.1, population_size)
        reinfection_probability_randomised = numpy.random.normal(0.9,0.4, population_size)
        recovery_time_randomised = numpy.random.randint(30, 100, population_size)
        # income_randomised = numpy.random.randint(50000, 100000, population_size)
        speed_randomised = numpy.random.randint(1, 10, population_size)
        mask_wearing_probability = numpy.random.normal(0.5,0.2,population_size)

        initialINF = int(self.population_size * self.initial_infected_percent)
        initialIMM = int(self.population_size * self.initial_immune_percent)

        """Economy Related"""
        quintilesCount = {}
        for quintile in range(5):
            qty = max(1.0, numpy.sum([1 for a in range(self.population_size) if social_stratum_randomised[a] == quintile and age_randomised[a] >= 18]))
            total = economyModel.lorenz_curve[quintile] * self.total_economy
            quintilesCount[quintile] = total / qty


        def create_agent(unique_id, index, infection_status, infection_severity, wealth):
            x, y = random.randrange(self.width), random.randrange(self.height)
            agent = PersonAgent(
                        unique_id = unique_id,
                        models = self,
                        x_pos = x,
                        y_pos = y,
                        infection_status = infection_status,
                        infection_severity = infection_severity,
                        infection_probability = infection_probability_randomised[index],
                        reinfection_probability = reinfection_probability_randomised[index],
                        recovery_time = recovery_time_randomised[i],
                        age = age_randomised[index],
                        social_stratum = social_stratum_randomised[index],
                        wealth = wealth,
                        mask_wearing_probability = mask_wearing_probability[index],
                        speed = speed_randomised[index],
                        amplitudes = self.amplitudes,
                        minimum_expense = self.minimum_expense,
                        hospital_limit = self.hospital_limit,
                        dist_spread = self.dist_spread,
                        )

            self.grid.place_agent(agent, (x, y))
            self.schedule.add(agent)

        # Generate Agents
        for i in range(self.population_size):
            if initialINF != 0:
                if(age_randomised[i]>=18): create_agent(i, i, "infected", "coolio", quintilesCount[social_stratum_randomised[i]])
                else: create_agent(i, i, "infected", "coolio", 0)
                initialINF-=1
                continue
            if initialIMM != 0:
                if(age_randomised[i]>=18): create_agent(i, i, "immune", "coolio", quintilesCount[social_stratum_randomised[i]])
                else: create_agent(i, i, "immune", "coolio", 0)
                initialIMM-=1
                continue
            if(age_randomised[i]>=18): create_agent(i, i, "susceptible", "coolio", quintilesCount[social_stratum_randomised[i]])
            else: create_agent(i, i, "susceptible", "coolio", 0)

        # Some metrics we'll measure about our model
        compute_SIR = compute_infected_count(self)
        self.datacollector = DataCollector(
            model_reporters={"infected Count": compute_infected_count, 
                             "susceptible Count": compute_susceptible_count, 
                             "immune Count": compute_immune_count}
            # agent_reporters={"Wealth": "wealth"},
        )

    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()

# Define agent-specific attributes and behaviors
class PersonAgent(Agent):
    def __init__(self, unique_id, models: VirusSpreadModel, x_pos, y_pos, infection_status, infection_severity,
                infection_probability, reinfection_probability, recovery_time, age,
                social_stratum: int, wealth, mask_wearing_probability, speed, amplitudes, minimum_expense,
                hospital_limit, dist_spread):
        super().__init__(unique_id, models)
        self.x= x_pos
        '''Initial x-coordinate'''
        self.y= y_pos
        '''Initial y-coordinate'''
        self.infection_status = infection_status
        '''"susceptible", "infected", "immune", "dead"'''
        self.infection_severity = infection_severity
        '''"exposed", "asymptomatic", "hospitalization", "severe"'''
        self.infection_probability = infection_probability
        '''Probability of getting infected'''
        self.reinfection_probability = reinfection_probability
        '''Probability of getting infected'''
        self.recovery_time = recovery_time
        '''Time it takes to recover'''
        self.days_infected = 0
        '''Time for which the agent is infected'''
        self.location = None
        '''Current Location of bob'''
        self.age = age
        '''bob's age'''
        self.no_time_infected = 0
        '''number of times bob has been infected'''
        self.social_stratum = social_stratum
        '''The social stratum (or their quintile in wealth distribution) of the agent'''
        # self.behavior = initial_behavior                      # bob's behaviorial traits
        # self.culture = initial_culture                        # bob's culture
        self.wealth = wealth
        '''bob's wealth'''
        self.social_contacts = set()
        '''bob's contacts'''
        # self.hygiene = initial_hygiene                        # bob's hygiene following
        self.mask_wearing_probability = mask_wearing_probability
        '''Probability of wearing a mask'''
        self.social_distancing_compliance = 0.0
        '''Probability of social distancing'''
        self.vaccinated = False
        '''Vaccination Status'''
        self.speed = speed
        '''Movement speed of bob'''
        
        ''' Extra Information '''
        self.amplitudes = amplitudes
        self.minimum_expense = minimum_expense
        self.hospital_limit = hospital_limit  
        self.dist_spread = dist_spread      
        self.models = models

    def step(self):
        self.move()
        self.update_self()
        self.interact()


    def move(self):
        if self.infection_status == "death" or (self.infection_status == "infected"
            and (self.infection_status == "hospitalization"
            or self.infection_severity == "severe")):
            return

        """ix = int(np.random.randn(1) * self.amplitudes[agent.status])
        iy = int(np.random.randn(1) * self.amplitudes[agent.status])

        if (agent.x + ix) <= 0 or (agent.x + ix) >= self.length:
            agent.x -= ix
        else:
            agent.x += ix

        if (agent.y + iy) <= 0 or (agent.y + iy) >= self.height:
            agent.y -= iy
        else:
            agent.y += iy"""

        # possible_steps = self.model.grid.get_neighborhood(
        #   self.pos,
        #   moore=True,
        #   include_center=True)
        ix = int(numpy.random.randn(1) * self.amplitudes[self.infection_status])
        iy = int(numpy.random.randn(1) * self.amplitudes[self.infection_status])

        new_position = [self.x + ix, self.y + iy]
        self.model.grid.move_agent(self, new_position)
        self.x += ix
        self.y += iy

        # Change Wealth of Agent
        self.change_wealth(ix, iy)

    def update_self(self):
        if self.infection_status == "death":
            return
        if self.infection_status == "infected":
            self.days_infected += 1

            indice = int(self.age // 10 - 1 if self.age > 10 else 0)

            teste_sub = numpy.random.random()

            if self.infection_severity == "asymptomatic":
                if economyModel.age_hospitalization_probs[indice] > teste_sub:
                    self.infection_severity = "hospitalization"
            elif self.infection_severity == "hospitalization":
                if economyModel.age_severe_probs[indice] > teste_sub:
                    self.infection_severity = "severe"
                    # self.get_statistics()
                    # if self.statistics['severe'] + self.statistics['hospitalization'] >= self.hospital_limit:
                    #     self.infection_status = "death"
                    #     self.infection_severity = "asymptomatic"

            death_test = numpy.random.random()
            if economyModel.age_death_probs[int(indice)] > death_test:
                self.infection_status = "death"
                self.infection_severity = "asymptomatic"
                return

            if self.days_infected > 20:
                self.days_infected = 0
                self.infected_status = "immune"
                self.infection_severity = "asymptomatic"
        self.wealth -= self.minimum_expense * economyModel.basic_income[int(self.social_stratum)]

    def interact(self):
        # Implement agent movement, interactions, and other behaviors
        # cellmates = self.model.grid.get_neighborhood([self.pos], 1, 1, self.dist_spread)
        cellmates = self.models.grid.get_neighbors(pos = [self.pos], moore = 1, radius = 3, include_center = True)
        if len(cellmates) > 1:
            for other in cellmates:
                if self.infection_status == "susceptible" and other.infection_status == "infected":
                    contagion_test = numpy.random.random()
                    self.infection_severity = "exposed"
                    if contagion_test <= self.infection_probability:
                        self.status = "infected"
                        self.infection_severity = "asymptomatic"

    # def get_statistics(self, kind='info'):
    #     """
    #     Calculate and return the dictionary of the population statistics for the current iteration.

    #     :param kind: 'info' for health statiscs, 'ecom' for economic statistics and None for all statistics
    #     :return: a dictionary
    #     """
    #     if self.statistics is None:
    #         self.statistics = {}
    #         for status in Status:
    #             self.statistics[status.name] = np.sum(
    #                 [1 for a in self.population if a.status == status]) / self.population_size

    #         for infected_status in filter(lambda x: x != InfectionSeverity.Exposed, InfectionSeverity):
    #             self.statistics[infected_status.name] = np.sum([1 for a in self.population if
    #                                                             a.infected_status == infected_status and
    #                                                             a.status != Status.Death]) / self.population_size

    #         for quintile in [0, 1, 2, 3, 4]:
    #             self.statistics['Q{}'.format(quintile + 1)] = np.sum(
    #                 [a.wealth for a in self.population if a.social_stratum == quintile
    #                  and a.age >= 18 and a.status != Status.Death])

    #     return self.filter_stats(kind)

    # def filter_stats(self, kind):
    #     if kind == 'info':
    #         return {k: v for k, v in self.statistics.items() if not k.startswith('Q') and k not in ('Business','Government')}
    #     elif kind == 'ecom':
    #         return {k: v for k, v in self.statistics.items() if k.startswith('Q') or k in ('Business','Government')}
    #     else:
    #         return self.statistics

    def change_wealth(self, ix, iy):
        dist = numpy.sqrt(ix ** 2 + iy ** 2)
        result_ecom = numpy.random.rand(1)
        self.wealth += dist * result_ecom * self.minimum_expense * (economyModel.basic_income[int(self.social_stratum)])

# Define a function to render the agents on the grid for visualization
def agent_portrayal(agent):
    colors = {
        "susceptible": "green",
        "infected": "red",
        "immune": "blue",
        "death": "black"
    }
    portrayal = {
        "Shape": "circle",
        "Filled": "true",
        "Layer": 0,
        "Color": colors[agent.infection_status],
        "r": 2
    }
    return portrayal

# Define the space dimensions (width and height)
width = 100
height = 100
#
# # Create a continuous space with the defined dimensions
# space = ContinuousSpace(width, height, torus=False)


# Create a canvas grid to display the model
grid = CanvasGrid(agent_portrayal, width, height, 500, 500)

chart1 = ChartModule([{'Label': 'susceptible Count',
                       'Color': 'Green'},
                      {'Label': 'infected Count',
                       'Color': 'Red'},
                      {'Label': 'immune Count',
                       'Color': 'Black'}],
  data_collector_name='datacollector')

chart2 = ChartModule([{
  'Label': 'infected Count',
  'Color': 'red'}],
  data_collector_name='datacollector')

chart3 = ChartModule([{
    'Label': 'immune Count',
    'Color': 'blue'}],
    data_collector_name='datacollector')

model_parameters={
                "population_size": Slider("Population Size", 500, 100, 1000, 50),
                "width": 100,
                "height":100,
                "intitial_infected_percent": Slider("Initial Infection Percentage", 0.05, 0, 1, 0.05),
                "initial_immune_percent": Slider("Initial Immune Percentage", 0.05, 0, 1, 0.05),
                "hospital_limit": Slider("Hospital Limit (in %)", 0.6, 0, 1, 0.05),
                "prob_spread": Slider("Probability Spread", 0.9, 0, 1, 0.05),
                "dist_spread": Slider("Spread Distance", 1, 0, 10, 0.5),
                "total_economy": Slider("Total initial Economy", 10000, 0, 1000000, 10000),
                "minimum_income": 1.0,
                "minimum_expense": 1.0,
                "amplitudes": {
                    "susceptible": 5,
                    "immune": 5,
                    "infected": 5},
                }


# Create a Mesa server for web-based visualization and set the port when launching
server = ModularServer(
    VirusSpreadModel,
    [grid,chart1],
    "Virus Spread Model",
    model_parameters
)
server.launch(port=8521)  # Specify the desired port here

'''
geospatial data open dataset
Chart.js

class InteractionSpace:
    def __init__(self, model):
        self.model = model
        # Define attributes specific to this interaction space

    def interact_with_agents(self):
        """
        Implement interactions with agents in this space.

        You can define the logic for interactions between agents
        in this space and any specific events or behaviors that
        occur within this space.
        """
        for agent in self.model.schedule.agents:
            # Implement interactions with agents in this space
            pass

    def update(self):
        """
        Implement any updates or changes to this interaction space
        that may occur over time. For example, you might update the
        state or conditions of the space.
        """
        pass

    def visualize(self):
        """
        Implement visualization of this interaction space if needed.
        This can be useful for visualizing the state of the space
        during the simulation.
        """
        pass

    # Add any additional methods or attributes specific to this space   Implement later
'''
