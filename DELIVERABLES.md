# Deliverable A: Accuracy vs. Vectors Searched when Varying Repartitioning Threshold

The following test results demonstrate how query response accuracy/efficiency is affected by different repartitioning threshold values.
Note that the below test evaluates all 200 questions at once
Some notes on the table below:
- "Average vectors searched"
    - Average searched vectors per question
    - TODO: EXPLAIN MORE
- "Average search fraction"
    - Vectors searched / Total vectors in corpus 
    TODO: EXPLAIN MORE
- "Average hit rate"
    - Each sample query in questions_scored.jsonl has an "oracle top-5" list, which stores the true 5 most similar stored embeddings to the query embedding
    - When presenting the system with a query, the searched storage node is selected based on the similarity of its centroid to the query embedding
    - The selected embeddings from the searched storage node are referred to as "hits"
    - Each embedding has an ID  
    - The hit rate is defined as len(expected_ids & actual_ids) / len(expected_ids), where expected_ids refers to the oracle top 5
    - This acts as a measure of accuracy of how similar the system's returned records are to the oracle records stored in the scored question file
- "Average returned score"
    - Every individual stored record has a "score." This score is the cosine similarity between its embedding and the query's embedding
    - When the system is presented a query, it retrieves the top k records (hits) most similar to the query in the selected storage node
    - This field refers to the overall score of the system's hits averaged across ALL questions
- "Average oracle score"
    - The top 5 oracle records (the 5 actual most similar records to the query) stored in the questions_scored.jsonl file also have a score
    - This field refers to the score of all the oracle records stored in the scored question file averaged across ALL questions
- "Average score accuracy"
    - Defined as (Average returned score) / (Average oracle score)
    - The output of the above calculation is a number between 0 and 1, and is a measure of accuracy of the records that the system retrieved when presented with queries
    - The closer the value is to 1, the more 
- "Overall score"
    - Defined as (Average score accuracy) / (Average search fraction)
    - Therefore this number represents an overall measure of performance, accounting for both the accuracy of the system's returned records and the number of vectors searched to obtain those records
    - The higher this number, the better the overall quality


| Repartition Threshold | Average vectors searched  | Average search fraction   | Average returned score    | Average oracle score  | Average score accuracy    | Average hit rate  | Overall score |
|-----------------------|---------------------------|---------------------------|---------------------------|-----------------------|---------------------------|-------------------|---------------|
| 1000                  | 520.42                    | 0.3940                    | 0.5634                    | 0.5812                | 0.9676                    | 0.7688            | 2.5888        |
| 800                   | 476.80                    | 0.3609                    | 0.5617                    | 0.5812                | 0.9650                    | 0.7500            | 2.7436        |
| 600                   | 316.12                    | 0.2393                    | 0.5521                    | 0.5812                | 0.9478                    | 0.6525            | 4.0847        |
| 400                   | 246.22                    | 0.1864                    | 0.5481                    | 0.5812                | 0.9400                    | 0.6360            | 5.1921        |
| 200                   | 134.44                    | 0.1018                    | 0.5375                    | 0.5812                | 0.9203                    | 0.5403            | 9.5754        |
| 100                   | 64.14                     | 0.0486                    | 0.5290                    | 0.5812                | 0.9079                    | 0.4808            | 20.5383       |



Analysis:

TODO



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
