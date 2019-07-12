from bleach import linkify

def build_links(text):
    return linkify(text)
