"""Register TC nodes to the tag

Every tag can have max 1 node registered to it.
And the node has other tags attached to it.

TagA is pointing to NodeA0, and NodeA0 has TagB/TagC.
In deep search for TagB, nodes attached with TagA also are included.

In MetaHub, node info doesn't need to be fully recorded, but the node_id and tag_ids.
"""