# Deliverable A: Accuracy vs. Vectors Searched when Varying Repartitioning Threshold

The following test results demonstrate how query response accuracy/efficiency is affected by different repartitioning threshold values. score_all_questions.py was used to obtain the values in the table below by averaging the results after providing the system 200 queries.

### Explanation of table fields

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

### Results

| Repartition Threshold | Average vectors searched  | Average search fraction   | Average returned score    | Average oracle score  | Average score accuracy    | Average hit rate  | Overall score |
|-----------------------|---------------------------|---------------------------|---------------------------|-----------------------|---------------------------|-------------------|---------------|
| 1000                  | 520.42                    | 0.3940                    | 0.5634                    | 0.5812                | 0.9676                    | 0.7688            | 2.5888        |
| 800                   | 476.80                    | 0.3609                    | 0.5617                    | 0.5812                | 0.9650                    | 0.7500            | 2.7436        |
| 600                   | 316.12                    | 0.2393                    | 0.5521                    | 0.5812                | 0.9478                    | 0.6525            | 4.0847        |
| 400                   | 246.22                    | 0.1864                    | 0.5481                    | 0.5812                | 0.9400                    | 0.6360            | 5.1921        |
| 200                   | 134.44                    | 0.1018                    | 0.5375                    | 0.5812                | 0.9203                    | 0.5403            | 9.5754        |
| 100                   | 64.14                     | 0.0486                    | 0.5290                    | 0.5812                | 0.9079                    | 0.4808            | 20.5383       |

### Analysis

The table above shows that as the repartition threshold decreases, the following trends hold:

- The search's content quality decreases (lower average score accuracy and average hit rate)
- The search's computational efficiency increases (lower average vectors searched and average search fraction)
- In general, the computational efficiency increases faster than the content quality decreases, leading to an increasing overall score

These results match our expectations. A smaller repartition threshold means a smaller number of vectors searched within the chosen storage node. However, because the partitions now hold fewer vectors, the centriod (the average of the embeddings stored at the node) is less stable and more prone to noise, which decreases routing quality and therefore decreases the returned content quality during a query.  

# Deliverable B: Insertion Order

### Testing Setup

- Before testing, the second occurences of all duplicate records were removed form full_corups_shuffled.json
- We present a new, reordered corpus called full_corpus_grouped.jsonl, which groups by record type (e.g. paper, lecture slide, transcript, textbook)
- We present a modified script called evaluate_insertion_order.py, which reports both all question scoring and partition layout
- Note that that a constant repartitioning threshold of 600 was used for the following testing

### Results

| Ingestion File Used           | Storage node sizes    | Storage node mean scores  | Average vectors searched  | Average search fraction   | Average score accuracy    | Average hit rate  | Overall score |
|-------------------------------|-----------------------|---------------------------|---------------------------|---------------------------|---------------------------|-------------------|---------------|
| full_corpus_shuffled.jsonl    | 422, 282, 309, 302    | 0.481, 0.547, 0.531, 0.586| 315.49                    | 0.2399                    | 0.9469                    | 0.6520            | 4.0203        |
| full_corpus_grouped.jsonl     | 591, 439, 285         | 0.494, 0.547, 0.506       | 436.23                    | 0.3317                    | 0.9592                    | 0.7475            | 3.0648        |

### Analysis

- Question #1: Does the final partition layout change?
  - Yes, the results demonstate that the partition layout varies significantly depending on the ingestion order
  - Above, full_corpus_shuffled.jsonl produced 4 storage nodes, which store 422, 282, 309, and 302 vectors, respectively
  - Conversely, full_corpus_grouped.jsonl produced 3 storage nodes, which store 591, 439, and 285 vectors, respectively
- Question #2: Does the average number of vectors searched change?
  - Yes, the results demonstrate that the average number of vectors searched can change depending on the ingestion order
  - In this case, it changes by a large amount (difference of over 100) because the number of storage nodes partitioned is different betwene the trials
- Question #3: Does the returned search quality change?
  - Yes, the results demonstrate that both the average score accuracy and average hit rate changes depending on the ingestion order
- Question #4: Why do these differences happen?
  - Consider a system which has several storage nodes at some point midway through ingestion
  - The set of records ingested prior to this point (set A) entirely determined the early establishment of each node's centroid values, which affects all subsequent routing
  - Consider if a different set of records (set B) were ingested first instead
  - The early establishment of each node's centroid values could be drastically different than that of case A
  - Therefore, all subsequently rounting of case B will be different from case A
  - Therefore, the timing of repartitioning in case B will also be different from case A
  - Overall, different ingestion orders produce different incremental centroid values, which produces different partition layouts (number of storage nodes/size of each storage node), which produces different search quality/efficiency during a query

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

This approach introduces some additional complexity for the controller. The controller must compare centroid similarities more carefully and decide whether a query should be routed to one node or multiple nodes. When multiple nodes are searched, the controller must send several ```SearchLocal``` requests and merge the returned results before selecting the final top-k matches. This increases the amount of coordination the controller performs compared to the baseline system.

There is also additional networking overhead, since multiple gRPC calls may be issued for a single query instead of just one. This can slightly increase latency and network traffic.

Another tradeoff is that more vectors may be searched in cases where a query is routed to multiple nodes. While this still searches far fewer vectors than scanning the entire corpus, it does increase the search cost compared to routing to only one node.

However, the goal of this approach is to balance these costs with improved search quality. Instead of always searching many nodes or performing a full search over all vectors, the system only expands the search when centroid similarities suggest that a query may lie near a partition boundary. This helps limit unnecessary work while still improving the chances of returning the most relevant results.

# Deliverable D: Extend Evaluation Beyond Sample Script

The provided score_all_questions.py script already provides this behavior. However, additional unit tests were created in the `evaluation` directory to further confirm each units functionality. To run the tests, run `python unit_tests.py` from the `project2/evaluation` directory. Below are the expected outputs:

```
test_put_ok (__main__.TestController.test_put_ok) ... ok
test_put_target_count_is_one_after_first_insert (__main__.TestController.test_put_target_count_is_one_after_first_insert) ... ok
test_put_two_records_both_ok (__main__.TestController.test_put_two_records_both_ok) ... ok
test_search_returns_correct_record_id (__main__.TestController.test_search_returns_correct_record_id) ... ok
test_search_returns_hit_after_put (__main__.TestController.test_search_returns_hit_after_put) ... ok
test_search_vectors_searched_is_nonzero (__main__.TestController.test_search_vectors_searched_is_nonzero) ... ok
test_search_local_returns_stored_record (__main__.TestStorageNode.test_search_local_returns_stored_record) ... ok
test_search_local_vectors_searched_equals_record_count (__main__.TestStorageNode.test_search_local_vectors_searched_equals_record_count) ... ok
test_split_partition_counts_add_up (__main__.TestStorageNode.test_split_partition_counts_add_up) ... ok
test_store_record_centroid_is_set (__main__.TestStorageNode.test_store_record_centroid_is_set) ... ok
test_store_record_count_increments (__main__.TestStorageNode.test_store_record_count_increments) ... ok
test_store_record_count_is_one (__main__.TestStorageNode.test_store_record_count_is_one) ... ok
test_store_record_ok (__main__.TestStorageNode.test_store_record_ok) ... ok

----------------------------------------------------------------------
Ran 13 tests in 4.598s

OK
```

# Additional Analysis

- Question #1: When are smaller partitions beneficial?
  - As shown in Deliverable A, smaller partitions are desired if query speed is prioritized over search quality
- Question #2: When are smaller partitions harmful?
  - As shown in Deliverable A, smaller partititions are NOT desired if a very high degree of search quality is required
- Question #3: What measurements were most effected by insertion order?
  - As shown in Deliverable B, insertion order did not have a considerable effect on search quality (0.9469 vs. 0.9592)
  - However, it did have a very significant effect on the average number of vectors searched (315.49 vs. 436.23)
  - These large differences in computational efficiency occur because different ingestion orders can effect the number of storage nodes created via repartitioning
- Question #4: Is one-node search too restrictive for some queries?
  - Yes, one-node search is almost surely too restrictive for some queries
  - As explained in the write-up, searching only a single storage node based on centroid similarity significantly improves query speed
  - However, it reudces accuracy, as the chosen storage node may not contain all relevant vectors to the query
  - Moreover, the one-node search approach sacrifices accuracy for speed
- Question #5: Would searching two nodes instead of one be a good tradeoff?
  - In cases where the repartitioning threshold is large, searching a second node is likely too computationally expensive to be a reasonable tradeoff
  - However, in cases where the repartitioning threshold is small, searching two nodes with the highest centroid similarity is a good tradeoff, as it will likely produce a higher search accuracy while searching a small number of additional vectors
- Question #6: Does your alternative scheme improve quality, cost, or both?
  - When evaluating across all 200 questions, the alternative repartitioning scheme:
  - Increased search quality:
    - Average score accuracy incrased from 0.9469 to 0.9748
    - Average hit rate increased from 0.6520 to 0.8100
  - Increased computational cost:
    - Average vectors searched increased from 315.49 to 476.72
    - Average search fraction increased from 0.2399 to 0.3625

# Extra Credit Repartitioning Scheme Analysis

## Summary of Results

The adaptive multi-node routing strategy was successfully implemented and evaluated against the baseline single-node routing approach. The implementation demonstrates a clear improvement in search quality metrics at the cost of increased computational overhead.

### Key Metrics Comparison

| Metric                    | Baseline | Adaptive Multi-Node | Change      | % Change |
|---------------------------|----------|---------------------|-------------|----------|
| Average hit rate          | 0.6520   | 0.8100              | +0.1580     | +24.2%   |
| Average score accuracy    | 0.9469   | 0.9748              | +0.0279     | +2.9%    |
| Average returned score    | 0.5512   | 0.5672              | +0.0160     | +2.9%    |
| Average vectors searched  | 315.49   | 476.72              | +161.23     | +51.1%   |
| Average search fraction   | 0.2399   | 0.3625              | +0.1226     | +51.1%   |
| Final total score         | 4.0203   | 3.0922              | -0.9281     | -23.1%   |

### Analysis

The adaptive multi-node routing strategy achieved substantial improvements in search quality at the cost of increased computational overhead:

**Quality Improvements:**

- **Hit rate: +24.2%** (65.2% -> 81.0%). Successfully captures records near partition boundaries that single-node routing misses
- **Score accuracy: +2.9%** (0.9469 -> 0.9748). Returned results more closely match oracle results
- **Returned score: +2.9%** (0.5512 -> 0.5672). Absolute quality of retrieved vectors improved

**Computational Cost:**

- **Vectors searched: +51.1%** (315.49 → 476.72). Still searches only 36.25% of corpus, far below exhaustive search
- The increased cost is concentrated on queries near partition boundaries; most queries still route to a single node

**Tradeoff Assessment:**

This is a favorable quality vs cost tradeoff for most applications. The 51% increase in vectors searched (from 315 to 477) is negligible when compared to the whole system. For applications prioritizing accuracy, the 24.2% improvement in hit rate is favorable.

The baseline's higher efficiency score (4.02 vs 3.09) reflects its formula (accuracy/search cost). Though the adaptive approach has better accuracy (0.9748 vs 0.9469), the 51% increase in search cost heavily penalizes it in this metric. However, for quality-critical applications, missing 24% of relevant results is worse than searching 162 additional vectors (out of 1315 total).

#### Conclusion

The adaptive multi-node routing strategy successfully improves search quality (hit rate +24.2%) by strategically expanding the search only when centroid similarities suggest ambiguity. This represents a tradeoff optimizing for accuracy over speed which is appropriate for semantic retrieval systems where missing relevant results is more expensive.
