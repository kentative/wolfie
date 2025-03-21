import re


def format_embed_fields(embed):
    formatted_string = ""
    for field in embed.fields:
        formatted_string += f"**{field.name}**\n{field.value}\n\n"
    return remove_emojis(formatted_string)


def remove_emojis(string: str):
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub('', string).strip()

