from typing import Dict, List, Callable

TRUE_PROPERTIES = set(["yes", "true", "1"])
FALSE_PROPERTIES = set(["no", "false", "0"])


def parse_boolean_property(value):
    return value in TRUE_PROPERTIES


def vehicle_property_getter(properties, vehicle):
    def get_property(name, parse_property=parse_boolean_property):
        _name = "{}:{}".format(name, vehicle)
        string_value = properties.get(_name, properties.get(name, ""))
        return parse_property(string_value)

    return get_property


def create_way_coefficient_calculator(
    coefficients: List[int] = [1, 2, 10, 100]
) -> Callable[[Dict, str, str], int]:
    """Create a function which can be used to find the cost coefficient for a way properties
    
    Arguments:
        coefficients {List[int]} -- Coefficients for cycle friendly, passible and impassible 
    
    Returns:
        Callable[[Dict, str, str], int] -- Function to find the 
    """

    def calculate_way_coefficient(
        properties: Dict, vehicle: str, direction="forward"
    ) -> int:
        """Check if a route is navigable by a given vehicle type 

        If the route is navigable return a positive number
        """

        if properties.get("cycleway"):
            return coefficients[0]

        get_property = vehicle_property_getter(properties, vehicle)

        oneway = get_property("oneway")
        if oneway and direction == "reverse":
            return coefficients[-1]

        bicycle = properties.get("bicycle", "")

        if bicycle in FALSE_PROPERTIES:
            return coefficients[-1]

        return {
            "yes": coefficients[0],
            "designated": coefficients[0],
            "permitted": coefficients[1],
        }.get(bicycle, coefficients[2])

    return calculate_way_coefficient
