# blue-montana

The (hypothetical) results of 2036 US election in Montana. Created as a study 
<br>in making choropleth map using self-made predictions on US politics.</br>
Not a political campaign or an endorsement of any kind.

### Prerequisites:

#### Python: ####

1. openpyxl (3.1.2) - reading .xlsx files. 
2. pandas (2.0.1) - working with tabular data.
3. plotly (5.14.1) - creating maps.
    1. psutil (5.9.5) - managing processes.
    2. requests (2.29.0) - accessing external resources.
4. wand (0.6.11) - converting svgs to pngs. 
  
#### Other: ####
1. Orca (1.3.1) - standalone application, writing maps to files.
2. ImageMagick (7.1.1.15) - required for wand to work. 

### Roadmap

- [x] Map data for presidential election - completed on 17-07-2023.
- [x] Map data for Senate election - completed on 17-07-2023.
- [ ] Map data for House election.
  - [ ] Create congressional district map.
- [ ] Map data for population change. 
- [ ] Add supporting legend and prettify. 


