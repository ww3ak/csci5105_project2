# Deliverable A: Accuracy vs. Vectors Searched when Varying Repartitioning Threshold

The following test results demonstrate how query response accuracy/efficiency is affected by different repartitioning threshold values. score_all_questions.py was used to obtain the values in the table below by averaging the results after providing the system 200 queries.

**Explanation of table fields:**

- "Average vectors searched"
    - Describes the average number of vectors in the chosen storage node searched per query to find the top k local hits best matching the query embedding 
- "Average search fraction"
    - (Average vectors searched) / (Total vectors in corpus)
    - This number is a measure of how efficiently the system finds the k local best hits
- "Average returned score"
    - Every stored record has a "score," which is the cosine similarity between its embedding and the query's embedding
    - This field refers to the overall score of the system's hits averaged across all 200 questions
- "Average oracle score"
    - Each item in the top 5 oracle list stored in the questions_scored.jsonl file also has a score
    - This field refers to the overall score of all oracle records averaged across all 200 questions
- "Average score accuracy"
    - Defined as (Average returned score) / (Average oracle score)
    - This number is a measure of hit accuracy (the closer it is to 1, the more similar the system's hits are to the oracle list contents) 
- "Average hit rate"
    - Each sample query in questions_scored.jsonl has an "oracle top-5" list, which stores the true 5 most similar stored embeddings to the query embedding
    - When presented with a query, the system searches extracts "hits" from the storage node with a centroid most closely matching the query embedding
    - The hit rate is defined as (Number of hits that are in the oracle list) / (Length of oracle list)
    - This acts as a measure of hit accuracy
- "Overall score"
    - Defined as (Average score accuracy) / (Average search fraction)
    - This is a measure of both the accuracy of the system's hits and efficiency at which it retrieved those hits

**Results:**

| Repartition Threshold | Average vectors searched  | Average search fraction   | Average returned score    | Average oracle score  | Average score accuracy    | Average hit rate  | Overall score |
|-----------------------|---------------------------|---------------------------|---------------------------|-----------------------|---------------------------|-------------------|---------------|
| 1000                  | 520.42                    | 0.3940                    | 0.5634                    | 0.5812                | 0.9676                    | 0.7688            | 2.5888        |
| 800                   | 476.80                    | 0.3609                    | 0.5617                    | 0.5812                | 0.9650                    | 0.7500            | 2.7436        |
| 600                   | 316.12                    | 0.2393                    | 0.5521                    | 0.5812                | 0.9478                    | 0.6525            | 4.0847        |
| 400                   | 246.22                    | 0.1864                    | 0.5481                    | 0.5812                | 0.9400                    | 0.6360            | 5.1921        |
| 200                   | 134.44                    | 0.1018                    | 0.5375                    | 0.5812                | 0.9203                    | 0.5403            | 9.5754        |
| 100                   | 64.14                     | 0.0486                    | 0.5290                    | 0.5812                | 0.9079                    | 0.4808            | 20.5383       |


**Analysis:**

The table above shows that as the repartition threshold decreases, the following trends hold: 

- The search's content quality decreases (lower average score accuracy and average hit rate)
- The search's computational efficiency increases (lower average vectors searched and average search fraction)
- In general, the computational efficiency increases faster than the content quality decreases, leading to an increasing overall score

These results match our expectations. A smaller repartition threshold means a smaller number of vectors searched within the chosen storage node. However, because the partitions now hold fewer vectors, the centriod (the average of the embeddings stored at the node) is less stable and more prone to noise, which decreases routing quality and therefore decreases the returned content quality during a query.  



# Deliverable B: Insertion Order

TODO

# Deliverable C: Propose Better Repartitiong Scheme

### Overview
With the goal of developing a repartitioning and routing scheme that improves search quality while minimizing the number of vectors searched, an adaptive multi-node routing strategy can be used. In this approach, the controller compares the similarity between the query embedding and the centroids of all storage nodes. If the highest-scoring centroid is significantly closer than the others and exceeds a predefined similarity threshold, the controller routes the query to only that node and performs a ```SearchLocal``` request there. However, if the top centroids have very similar similarity scores, the controller routes the query to multiple nodes and performs ```SearchLocal``` requests on each of them. This indicates that the query may lie near a partition boundary, where relevant records could exist in more than one partition. By routing queries to additional nodes only when necessary, this strategy reduces unnecessary searches while preserving search quality for ambiguous queries.

### Metadata
Since this approach relies on the existing metadata from the original system, no significant additions would be required. The **controller** would continue to rely on the: **target address, the centroid, and the number of vectors stored on each node.** Similarly, the **storage nodes** would continue to maintain their **local records, centroid and vector count.**

However, a new **similarity threshold parameter** would be introduced. This parameter would allow the controller to determine whether a query should be routed to only one node or to multiple nodes when centroid similarities are very close.


### Routing
In this proposed repartitioning scheme, the controller still computes the similarity between the query embedding and all node centroids. What differs from the baseline system is the final routing decision.

Instead of always routing the query to a single node, the decision becomes more flexible and depends on the similarity scores of the top centroids. If the centroid with the highest score is clearly the best match and exceeds a set similarity threshold, the controller routes the query to only that node.

However, if multiple centroids have similarly high scores, the controller routes the query to multiple nodes. Each of those nodes performs a SearchLocal operation. The controller then combines the returned results and selects the global top-k matches before returning the final response to the client. This approach allows the system to search additional partitions only when the query appears to lie near a partition boundary, which can help improve the accuracy of the returned results.


### Repartitioning
The repartitioning process would remain mostly the same as in the baseline system. When a storage node exceeds the configured vector threshold, the controller creates a new storage node container and instructs the overloaded node to perform a ```SplitPartition```.

During this process, the node runs a local k = 2 split over its stored vectors. One cluster remains on the original node, while the other cluster is transferred to the new node using the ```ReplaceLocalPartition``` RPC. Both nodes then recompute their centroids and return their updated metadata to the controller.

Even if related vectors are split across neighboring nodes, adaptive routing allows queries near those boundaries to search both partitions.

### Accuracy vs. Search-cost - Tradeoff
In the baseline system, a query is always routed to a single node. This keeps the number of vectors searched low, but reduces accuracy when relevant records are stored in a neighboring partition. With the adaptive routing approach, most queries are still routed to only one node, which keeps the search cost low. However, when the computed top centroid values are similar, it suggest that a query is near a partition boundary, and the controller can route the query to multiple nodes, and therefore combine the returned results, choose a global top-k match and return a more accurate response to the client. This increases the chances of retrieving the most relevant records while still searching only a small portion of the total corpus. As a result, the system can improve search quality without significantly increasing the average number of vectors searched.


### New Complexities
This approach introduces some additional complexity for the controller. The controller must compare centroid similarities more carefully and decide whether to route the query to one node or multiple nodes. In cases where multiple nodes are searched, the controller has to send multiple ```SearchLocal``` requests and merge the returned results before selecting the final global top-k matches.

The additional calculation and messages may slightly increase network traffic and the number of vectors searched for some queries. However, since additional nodes are only searched when necessary, the overhead remains similar to the baseline systems repartitioning scheme and overall is relatively small compared to searching the entire corpus.

# Deliverable D: Extend Evaluation Beyond Sample Script

TODO
Basically already done becuase of the provided score_all_questions.py script. From Mitch: "We ended up giving that code to you so deliverable D is not all that relevant, but if you need to make modifications to the various evaluation scripts to achieve the other deliverables and/or the extra credit that is okay and likely necessary."
