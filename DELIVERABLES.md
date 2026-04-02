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

TODO

# Deliverable D: Extend Evaluation Beyond Sample Script

TODO
Basically already done becuase of the provided score_all_questions.py script. From Mitch: "We ended up giving that code to you so deliverable D is not all that relevant, but if you need to make modifications to the various evaluation scripts to achieve the other deliverables and/or the extra credit that is okay and likely necessary."