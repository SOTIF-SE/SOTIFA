# SOTIFA: STPA-Guided SOTIF Assessment of Real-Time Behavior of the Autonomous Driving System under Uncertain Environments

This repository presents a new SOTIF(Safety Of The Intended Functionality) assessment tool for ADS----SOTIFA. It can systematically evaluate the SOTIF risk of different desgin models of ADS(Automated Driving System) under uncertain environment.

## Overview

- Our method can systematically evaluate the safety of autonomous vehicles in an open and uncertain environment, and quantify the ADS **SOTIF risk**.
  In order to be more adaptable to the SOTIF evaluation, the attribute set called **"EnvAADL"** is extended, which aims to capture the hybrid external dynamic environment.
  In this way, engineers can easily develop and understand ADS with EnvAADL(Environmental Architecture Analysis and Design Language), and in addition, they can supplement additional key information on the established AADL model to evaluate, so that the original AADL model can be reused. For the huge state space brought by continuous behaviors and uncertain environments, we provide **efficient mechanisms HCV(Hazard Confidence Value) ** to quantify them, thus giving the tool **SOTIFA** end-to-end SOTIF assessment based on STPA(Systems-Theoretic Process Analysis).

## Dependencies:

We conducted the experiment using the tool chain under the following environments. We hope it can work under other operating systems and tool versions as well.

- Operating System: Ubuntu 22.04.2
- Pre-installed software:
  - [java 17.0.8](https://www.oracle.com/java/technologies/downloads/#java17)
  - [osate2-2.11.0](https://osate-build.sei.cmu.edu/download/osate/stable/2.11.0/products/)
  - [Neo4j 5.10.0(COMMUNITY)](https://neo4j.com/deployment-center/#releases)

Our tool uses the environment above. After install the tools, we also need to import the information we need:

- **Copy lib to /usr/lib**

```
sudo cp -r lib/* /usr/lib/
```

- **Copy script.sh to /tmp/tempDirectory**

```
mkdir -p /tmp/tempDirectory && cp script.sh /tmp/tempDirectory/
```

-/path/to/script.sh replaced with the current script.sh path

- **Import the Knowledge Graph**

Navigate to the 'bin' directory within the installation directory of Neo4j.
```
./neo4j-admin database load --from-path=/home/cxy/SOTIFATools neo4j --overwrite-destination=true
neo4j start
```
-/path/to/neo4j replaced with the current neo4j path
-set USER is `neo4j`, PASSWORD is `12345678`

- **Install the EnvAADL plugin on OSATE2**

```
Help -> install new Software -> Add -> Local ->SOTIFASite
```

## Structures:

```
SOTIFA
├──SOTIFA Installation_Usage Videos
│      ├── SOTIFA Installation.mp4
│      └── SOTIFA Usage.mp4
├── CARLA reproduction
├── Experiment result
│      └── results
└── SOTIFATools
│      ├── SOTIFASite
│      ├── lib
│      └── script.sh
└── env-self-driving-car
│        └── case-study
│        │    ├── ADSsimpleDesign.aadl
│        │    └── ADSmultiStageDesign.aadl
│        └── DynamicsBaseTypes
│        └── EnvAADLAnalysis
└── README
```
We have provided installation and usage videos for SOTIFA `SOTIFA Installation.mp4 ` and `SOTIFA Usage.mp4 `

This project contains experiment result.

- `SOTIFASite`: SOTIFASite plug-in files can be installed.
- `lib`: The required libraries of the assessment.
- `env-self-driving-car`: The EnvAADL project, which contains the two designs and their files.
  To evaluate the efficacy of the SOTIF of EnvAADL of ADS, we also include two case studies in the sub-directory named `examples`. For each case studies, the subsub-director contains two AADL files, the XML files are generate from .aadl model. One is the “ADSsimpleDesign”, and the other is “ADSmultiStageDesign”. The details are as follows:

- “ADSsimpleDesign”: The vehicle initially travels at a speed of 10. Upon nearing a distance of 0.5 from other actors (excluding the environmental car), it initiates deceleration. Otherwise, it maintains a distance of 20 from the preceding vehicle. Deceleration occurs when the distance from the leading vehicle is 20, while acceleration resumes when the distance exceeds 20. These specifications are stored in `ADSsimpleDesign.aadl`, with the corresponding Hybrid Automata being automatically generated and labeled as `ADSsimpleDesignProduct.xml`.

- “ADSmultiStageDesign”: This EnvAADL design integrates a multi-stage acceleration/deceleration mechanism. Upon nearing a distance of 10 from other actors (excluding the environmental car), it begins decelerating, taking into account the vehicle's speed. Within this model, acceleration can be dynamically adjusted based on both speed and distance. It is saved as `ADSmultiStageDesign.aadl`, with the automatically generated Hybrid Automata being named `ADSmultiStageDesignProduct.xml`.


## Usage:

To demonstrate the usage of our tool-chain, we use the `ADS` as an example. We assume that you have installed all the dependent software as mentioned before. Typically, the usage of SOTIFA involves following steps：

1. **Modeling** : You can use the OSTAE2 tool to model your EnvAADL designs. Since we have done the modeling of the `ADS` scenario, in this example you can directly load the EnvAADL project named `env-self-driving-car` in OSATE2. If you want to extend the model, you can modify the AADL design.

- Various components exchange data via shared variables. The plant, controller, and environment components are extracted into hybrid automata. And the system is product automata of hybrid automata which are  extracted from the plant, controller, and environment components.

- Modify the system's environmental parameters, control parameters and control modes without altering the component structure to assess the SOTIF risk associated with different control strategies.

2. **Quantitative analysis** :
   - Export the AADL model designed in step 1 into an XML file. (Select the project `ADSsimpleDesign.aadl`, right-click -> Open With -> "Sample Ecore Model Editor" -> File -> Save as -> File name: `ADSsimpleDesign.aaxl2` -> EnvAADLAnalysis/currentXML -> OK -> rename it as `ADSsimpleDesign.xml`)
   In this example, the XML file `ADSsimpleDesign.xml` and `ADSmultiStageDesign.xml`in EnvAADLAnalysis/currentXML.
     
   - Click `SOTIFA` -> `SOTIF assessment under uncertain environment` to get the SOTIF assessment risk.
