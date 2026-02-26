"""
Data and actual tags are stored in TC, the relationships of tags are stored in MetaHub.

1. Hold a snapshot of tag relationships in TC, and calculate the relationships or filter the items.
   Mostly done in TC.

2. Let the client to render tags (or fetch relationships from MetaHub), TC backend only returns raw tag_ids.

3. Ask MetaHub to calculate the relationships, return a list of relevant tag_ids.
   Use client to render the tags.
   TC only filter the provided tags.
"""