# Core Domain Model

## World
- Map
- Region
- Biome
- Coordinate Reference
- Geometry

## Creatures
- Creature
- Creature Variant
- Creature Spawn
- Spawn Region
- Spawn Container
- Creature Drop
- Harvest Resource
- Taming Profile
- Breeding Profile
- Creature Stat Profile
- Dossier

## Items
- Item
- Item Category
- Blueprint
- Engram
- Crafting Recipe
- Crafting Station
- Repair Station

## Loot
- Loot Source
- Loot Set
- Loot Entry
- Quality Profile

## Bosses
- Boss
- Boss Variant
- Arena
- Boss Tribute
- Boss Reward
- Tekgram

## Lore
- Explorer Note
- Dossier
- Story Entry

## Evidence
- Source
- Evidence Record
- Verification Event
- Data Revision

## Reference relationship

`Creature → uses Item → has Blueprint → appears in Loot Entry → belongs to Loot Set → emitted by Loot Source → located on Map`

`Creature → has Variant → spawns through Spawn Container → intersects Spawn Region → belongs to Map`
