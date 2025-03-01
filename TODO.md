1. ~~Refactor wonder_conquest to use base class~~
2. ~~Clean up core module, use async~~
3. Refactor to use Single cog data interactions design 
4. Implement Multi cog data interaction
5. Implement Agentic cog interaction


# Design
## Structure
bot
- core
  - thalamus (sensory transmission, motor signals)
    - provide data from multiple cogs: (get_xxx)
  - cortex (neocortex, high order thinking)
  - ganglia (motor control, procedural memory, habit)
    - provide data from a single cog: (get_cog_data, update_cog_data)
    - persist data (i.e., data/cog_data.json)
      - preferences: CogData
      - queues: CogData
      - battles: CogData

- cogs
  - preferences: store user settings and preferences
  - queue: allow user to submit request for specific titles. User requests are queued.
  - battle: assists with battle registration details


## Data Flow
1. Single cog data interactions (i.e., preferences.add, prefs.list)
   - **direct memory access, no need to go through thalamus**
   - cog1 <-> ganglia <-> cog1.data
   - cog1 <-> ganglia <-> cog2.data

2. Multi cog data interaction (i.e., queue.add, dawn.list)
   - **requires multiple calls to ganglia, go through thalamus**
   - cog1 <-> thalamus <-> (ganglia.1, ganglia.2)

3. Agentic cog interaction (i.e., add me to wonder battle this weekend)
   - **require multi interaction between cog and cog data**
   - cog1 <-> cortex <-> (thalamus.1, thalamus.2)
   - cog1 <-> (cortex.1, cortex.2)

  