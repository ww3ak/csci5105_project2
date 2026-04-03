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

TODO

# Deliverable D: Extend Evaluation Beyond Sample Script

TODO
Basically already done becuase of the provided score_all_questions.py script. From Mitch: "We ended up giving that code to you so deliverable D is not all that relevant, but if you need to make modifications to the various evaluation scripts to achieve the other deliverables and/or the extra credit that is okay and likely necessary."