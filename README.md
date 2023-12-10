# SOTIFA: STPA-guided end-to-end SOTIF assessment of real-time behavior of the autonomous driving system under uncertain environment

This repository presents a new SOTIF(Safety Of The Intended Functionality) assessment tool for ADS----SOTIFA. It can systematically evaluate the SOTIF safety of different desgin models of ADS(Automated Driving System) under uncertain environment.

## Overview

- Our method can systematically evaluate the safety of autonomous vehicles in an open and uncertain environment, and quantify the ADS **SOTIF risk**.
  In order to be more adaptable to the SOTIF evaluation, the attribute set called **"Hybrid_EnvAADL"** is extended, which aims to capture the hybrid external dynamic environment.
  In this way, experts can easily develop and understand ADS with EnvAADL(Environment Architecture Analysis and Design Language), and in addition, they can supplement additional key information on the established AADL model to evaluate, so that the original AADL model can be reused. For the huge state space brought by continuous behaviors and uncertain environments, we provide **efficient mechanisms** to quantify them, thus giving the tool **SOTIFA** end-to-end SOTIF assessment based on STPA(Systems-Theoretic Process Analysis).

## Dependencies:

We conducted the experiment using the tool chain under the following environments. We hope it can work under other operating systems and tool versions as well.

- Operating System: Ubuntu 22.04.2
- Pre-installed software:
  - [java 17.0.8](https://www.oracle.com/java/technologies/downloads/#java17)
  - [osate2-2.11.0](http://aadl.info/aadl/osate/stable/2.2.1/products/)

Our tool uses the environment above. After install the tools, we also need to import the information we need:

- **Copy lib to /usr/lib**

```
sudo cp -Rf . /usr/lib
```

- **Copy script.sh to /tmp/tempDirectory**

```
mkdir -p /tmp/tempDirectory && cp /path/to/{script.sh,AETG,getTree} /tmp/tempDirectory/
```

-/path/to/script.sh replaced with the current script.sh path

- **Install the EnvAADL plugin on OSATE2**

```
Help -> install new Software -> Add -> Local ->SotifaSite
```

## Structures:

```
SOTIFA
├──SOTIFA Installation_Usage Videos
│      ├── SOTIFA Installation.mp4
│      └── SOTIFA Usage.mp4
├── Experiment result
│      └── results
└── SotifaTools
│      ├── Sotifasite
│      ├── lib
│      └── script.sh
└── env-self-driving-car
│        └── case-study
│        │    ├── simpleDesign.aadl
│        │    └── MultiStageDesign.aadl
│        └── DynamicsBaseTypes
│        └── EnvAADLAnalysis
└── README
```
We have provided installation and usage videos for SOTIFA `SOTIFA Installation.mp4 ` and `SOTIFA Usage.mp4 `

This project contains experiment result.

- `SotifaSite `: SotifaSite plug-in files can be installed.
- `lib `: The required libraries of the assessment.
- `env-self-driving-car `: The EnvAADL project, which contains the two designs and their files.
  To evaluate the efficacy of the SOTIF of EnvAADL of ADS, we also include two case studies in the sub-directory named `examples`. For each case studies, the subsub-director contains two AADL files, the XML files are generate from .aadl model. One is the “Simple design”, and the other is “consider multi-stage acceleration/deceleration design”. The details are as follows:

- “Simple design”: Initially, the vehicle runs at an initial speed of 10. And keep a distance of 50 from the vehicle in front. The vehicle slows down when the distance from the front vehicle is 50, and speeds up when the distance is greater than 50. It is saved as named `simpleDesign.aadl` and the automatically generated Hybrid Automata named `simpleDesignProduct.xml `.

- “Multi-Stage design”: This EnvAADL design incorporates a multi-stage acceleration/deceleration process. It is divided into several modes: Closing, Coasting, Matching, Braking. And in this model, the safe distance can be adjusted according to the speed. It is saved as named `MultiStageDesign.aadl` and the automatically generated Hybrid Automata named `MultiStageDesignProduct.xml `.

## Usage:

To demonstrate the usage of our tool-chain, we use the Cooperative Adaptive Cruise Control (CACC) as an example. We assume that you have installed all the dependent software as mentioned before. Typically, the usage of SOTIFA involves following steps：

1. **Modeling** : You can use the OSTAE2 tool to model your EnvAADL designs. Since we have done the modeling of the CACC scenario, in this example you can directly load the EnvAADL project named `env-self-driving-car` in OSATE2. If you want to extend the model, you can modify the AADL design.

2. **Quantitative analysis** :
   - Export the AADL model designed in step 1 into an XML file. In this example, the XML file `simpleDesign.xml` and `MultiStageDesign.xml`.
     
   - Click `SOTIFA` -> `SOTIF assessment under uncertain environment`
