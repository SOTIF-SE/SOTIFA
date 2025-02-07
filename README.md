# A STPA-Guided SOTIF Assessment of Real-Time Autonomous Driving Behavior in Uncertain Environments

This repository presents a new SOTIF(Safety Of The Intended Functionality) assessment tool for ADS----SOTIFA. It can systematically evaluate the SOTIF risk of different design models of ADS(Automated Driving System) under uncertain environment.

## Overview


- The method systematically evaluates the safety of autonomous vehicles in open and uncertain environments, quantifying the ADS **SOTIF risk**.To enhance SOTIF evaluation adaptability, we extend the property set **"EnvAADL"**, which captures hybrid external dynamic environments. Engineers can use EnvAADL (Environmental Architecture Analysis and Design Language) to develop and understand ADS efficiently, supplement key information in existing AADL models, and reuse them for assessment. To address the huge state space caused by continuous behaviors and uncertain environments, we provide efficient HCV (Hazard Confidence Value) mechanisms for quantification, enabling **SOTIFA** to perform end-to-end SOTIF assessment based on STPA (Systems-Theoretic Process Analysis).


## Installation:

We conducted the experiment using the tool chain under the following environments. We hope it can work under other operating systems and tool versions as well.

- Operating System: Ubuntu 22.04.2
- Pre-installed software:
  - [java 17.0.8](https://www.oracle.com/java/technologies/downloads/#java17)
  - [osate2-2.11.0](https://osate-build.sei.cmu.edu/download/osate/stable/2.11.0/products/)
  - [Neo4j 5.10.0(COMMUNITY)](https://neo4j.com/deployment-center/#releases)

SOTIFA uses the environment above. After install the tools, we also need to import the information we need:

- **Copy lib to /usr/lib**

```
sudo cp -r lib/* /usr/lib/
```

- **Import the Knowledge Graph**

Navigate to the 'bin' directory within the installation directory of Neo4j.
```
./neo4j-admin database load --from-path=/home/cxy/SOTIFATools neo4j --overwrite-destination=true
neo4j start
```
- Replace `/path/to/neo4j` with the actual Neo4j path.
- Set USER as `neo4j`, PASSWORD as `12345678`.

- **Install the EnvAADL plugin on OSATE2**

```
Help -> install new Software -> Add -> Local ->SOTIFASite
```
## Running SOTIFA:


This guide provides an overview of how to use SOTIFA for assessing SOTIF risks in autonomous driving systems (ADS). Ensure all dependencies are installed before proceeding.

### Steps to Use SOTIFA

#### 1. EnvAADL Modeling
Import the `env-self-driving-car/` project or create your own.

- The system consists of hybrid automata extracted from plant, controller, and environment components.

- <img src="README.source/top+plant.pdf" alt="top+plant" style="zoom:66%;" />
- <img src="README.source/tcontroller+env.pdf" alt="tcontroller+env" style="zoom:66%;" />

- ##### Main components:
- - **Plant Component**: Models the ego car’s dynamics with initial values (like `x_ego = 0`, `v_ego = 10`, `a_ego = 0`).
- - **Environment Component**: Defines external factors (e.g., friction, slope) and dynamic actors (e.g., environmental vehicles).
- - **Controller Component**: Samples ego car and environmental parameters, then calculates acceleration to maintain a safe distance of 10 units from the preceding vehicle.



#### 2. SOTIF assessment
 Run the assessment:
   - Click `SOTIFA` -> `SOTIF assessment under uncertain environment` to analyze risks.

- <img src="README.source/tool interface.pdf" alt="interface" style="zoom:66%;" />

- The middle panel displays the EnvAADL model code for the ADS in the illustrated case (Sec. II-B). The assessment process begins with `SOTIFA` performing static checks to ensure EnvAADL syntax compliance. Users initiate the assessment by selecting `SOTIFA` → `SOTIF assessment under uncertain environment` at the top, prompting the tool to parse the `EnvAADL` file and update the right panel with the hazard analysis tree and the SOTIF risk score (Sec. VI). Upon running the assessment, an `EnvAADLAnalysis` folder is generated on the left, containing intermediate analysis files, including automata files extracted from `EnvAADL` (Sec. IV-B), EUCAs-based specification files (Sec. V), and final analysis results in the `analysisResults` folder, which contains the hazard analysis tree annotated with scores (Sec. VI).


## Structures:

```
SOTIFA
├──SOTIFA Installation_Usage Videos
│      ├── SOTIFA Installation.mp4
│      └── SOTIFA Usage.mp4
└── SOTIFATools
│      ├── lib
│      ├── SOTIFASite
│      └── neo4j.dump
└── env-self-driving-car
│        └── case-study
│        │    ├── ADSHighAggressive.aadl
│        │    └── ADSLowAggressive.aadl
│        └── EnvAADL
│        └── EnvAADLAnalysis
└── README
```

This project contains experiment result:

- ####  Case Studies -`env-self-driving-car`

- - #### ADSHighAggressive
- - - The system completely disregards emergency braking and adherence to traffic regulations, maintaining a distance of 10 from the preceding vehicle.
- - - Model: `ADSHighAggressive.aadl`
- - - Generated Automata: `ADSHighAggressiveProduct.xml`

- - #### ADSLowAggressive
- - - The system considers emergency braking and adherence to traffic regulations, decelerating at a distance of 30 from the preceding vehicle. The system is refined by optimizing acceleration and deceleration controls.
- - - Model: `ADSLowAggressive.aadl`
- - - Generated Automata: `ADSLowAggressiveProduct.xml`


- ####  SOTIFATools
- - `SOTIFASite`: SOTIFASite plug-in files can be installed.
- - `lib`: The required libraries of the assessment.
- - `neo4j dump`: The knowledge graph.

-  #### Additional Resources
- Installation and usage videos are available:
- - `SOTIFA Installation.mp4`
- - `SOTIFA Usage.mp4`


