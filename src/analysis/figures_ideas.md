# Twelve Key Data Visualizations

## 1. **Session Activity Timeline**
- **Type**: Line chart with dual axes
- **Content**: Number of sessions and queries over time (daily/weekly), with phase markers (Alpha, Beta closed, Beta open)
- **Purpose**: Show adoption patterns and activity peaks

## 2. **User Audience Distribution**
- **Type**: Stacked bar chart or donut chart
- **Content**: Breakdown by user category (researchers, students, ITA, journalists, other) with sub-categories showing affiliation
- **Purpose**: Understand who uses the system

## 3. **Query Type Classification**
- **Type**: Treemap or hierarchical bar chart
- **Content**: Query categories (publication search, topic summary, author information, methodology questions, etc.) with frequency
- **Purpose**: Identify main use cases

## 4. **Session Depth Distribution**
- **Type**: Histogram
- **Content**: Number of interactions per session (1-5, 6-10, 11-20, 21+ messages)
- **Purpose**: Understand engagement levels (already partially shown in uploaded notebook)

## 5. **Response Quality Metrics Dashboard**
- **Type**: Multi-panel gauge/scorecard
- **Content**: Citation accuracy rate, hallucination incidents, user satisfaction (thumbs up/down ratio), response completeness score
- **Purpose**: Quantify system performance

## 6. **Cost Analysis Over Time**
- **Type**: Stacked area chart
- **Content**: Daily/weekly costs broken down by component (LLM API calls, hosting, storage) with cumulative total
- **Purpose**: Track financial sustainability

## 7. **RAG Engine Comparison Matrix**
- **Type**: Heat map or radar chart
- **Content**: Performance metrics (response time, accuracy, citation quality, cost-per-query) across tested engines (R2R, LlamaIndex, PaperQA, etc.)
- **Purpose**: Support technology selection decisions

## 8. **Citation Network Visualization**
- **Type**: Network graph
- **Content**: Most-cited publications as nodes, with connections showing co-citation patterns, sized by citation frequency
- **Purpose**: Reveal which research is most accessed

## 9. **Response Time vs. Query Complexity**
- **Type**: Scatter plot with trend line
- **Content**: X-axis = query length/complexity metrics, Y-axis = response time, color-coded by user satisfaction
- **Purpose**: Identify performance bottlenecks

## 10. **Environmental Impact Breakdown**
- **Type**: Sankey diagram
- **Content**: Energy flow from source through computation types (indexing, retrieval, generation) to CO2 emissions
- **Purpose**: Visualize sustainability profile

## 11. **User Journey Funnel**
- **Type**: Funnel chart
- **Content**: Steps from landing → registration → first query → multiple interactions → feedback provided, with drop-off rates
- **Purpose**: Identify user experience friction points

## 12. **Topic Coverage Heat Map**
- **Type**: Matrix heat map
- **Content**: CIRED research themes (rows) × query frequency and response quality (columns), color intensity showing coverage
- **Purpose**: Identify well-covered vs. underserved research areas

---

Each visualization should include:
- Clear title and axis labels
- Source data notes
- Interpretation guidance
- Interactive version link where applicable
- Accessibility considerations (color-blind friendly palettes)
