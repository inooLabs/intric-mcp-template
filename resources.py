def tell_a_joke() -> str:
    """
    Provides a joke
    """
    return "A neutron walks into a bar and says 'I'd like a beer please, how much?', the bartender says 'for you, no charge.' "


def get_past_weather(city: str, date: str) -> dict:
    """Provide the past weather for a given city and date."""
    return {"city": city, "date": date, "temperature": 15, "description": "Cloudy", "units": "C"}
