# A STPA-Guided SOTIF Assessment of Real-Time Autonomous Driving Behavior in Uncertain Environments

This repository presents a new SOTIF(Safety Of The Intended Functionality) assessment tool for ADS----SOTIFA. It can systematically evaluate the SOTIF risk of different design models of ADS(Automated Driving System) under an uncertain environment.

## Overview


- The method systematically evaluates the safety of autonomous vehicles in open and uncertain environments, quantifying the ADS **SOTIF risk**.To enhance SOTIF evaluation adaptability, we extend the property set **"EnvAADL"**, which captures hybrid external dynamic environments. Engineers can use EnvAADL (Environmental Architecture Analysis and Design Language) to develop and understand ADS efficiently, supplement key information in existing AADL models, and reuse them for assessment. To address the huge state space caused by continuous behaviors and uncertain environments, we provide efficient ERV (EUCA Risk Value) mechanisms as a reference value for quantification, enabling **SOTIFA** to perform end-to-end SOTIF assessment based on STPA (Systems-Theoretic Process Analysis).


## Installation:

We conducted the experiment using the tool chain under the following environments. We hope it can work under other operating systems and tool versions as well.

- Operating System: Ubuntu 22.04.2
- Pre-installed software:
  - [java 17.0.8](https://www.oracle.com/java/technologies/downloads/#java17)
  - [osate2-2.11.0](https://osate-build.sei.cmu.edu/download/osate/stable/2.11.0/products/)
  - [Neo4j 5.10.0(COMMUNITY)](https://neo4j.com/deployment-center/#releases)

SOTIFA uses the environment above. After installing the tools, we also need to import the information we need:

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


#### 1. 📐 EnvAADL Modeling

Import the `env-self-driving-car/` project or create your own.

- The system consists of hybrid automata extracted from plant, controller, and environment components.

<img src="README.source/top+plant.jpg" alt="top+plant" width="600px" />
<img src="README.source/tcontroller+env.jpg" alt="tcontroller+env" width="600px" />

##### 🔧 Main Components

- **Plant Component**  
  Models the ego car’s dynamics with initial values (like `x_ego = 0`, `v_ego = 10`, `a_ego = 0`).

- **Environment Component**  
  Defines external factors (e.g., friction, slope) and dynamic actors (e.g., environmental vehicles).

- **Controller Component**  
  Samples ego car and environmental parameters, then calculates acceleration to maintain a safe distance from the preceding vehicle.

> **Note:** ***perception modeling***. Crucially, this component also formalizes how variable atmospheric conditions, such as weather and visibility, impact the perception system. To achieve this, the component interfaces with a knowledge graph that maps specific conditions (e.g., ‘visibility<50') to quantifiable perception error magnitudes. This allows the framework to dynamically generate a realistic perception_error value, which is then used by the vehicle's control model to simulate how real-world environmental effects can lead to potential SOTIF-related risks.

---

#### 2. 📉 SOTIF Assessment

Run the assessment:

- Click `SOTIFA` → `SOTIF assessment under uncertain environment` to analyze risks.

<img src="README.source/tool interface.jpg" alt="interface" width="600px" />

The middle panel displays the EnvAADL model code for the ADS in the illustrated case (Sec. II-B). The assessment process begins with `SOTIFA` performing static checks to ensure EnvAADL syntax compliance. Users initiate the assessment by selecting `SOTIFA` → `SOTIF assessment under uncertain environment` at the top, prompting the tool to parse the `EnvAADL` file and update the right panel with the hazard analysis tree and the SOTIF risk score (Sec. VI). Upon running the assessment, an `EnvAADLAnalysis` folder is generated on the left, containing intermediate analysis files, including automata files extracted from `EnvAADL` (Sec. IV-B), EUCAs-based specification files (Sec. V), and final analysis results in the `analysisResults` folder, which contains the hazard analysis tree annotated with scores (Sec. VI).




## Structures:

```
SOTIFA
├──SOTIFA Installation_Usage Videos
│      ├── SOTIFA Installation.mp4
│      └── SOTIFA Usage.mp4
├──CARLA-based_Reproduction
│      ├── Case1_Random_Actor
│      ├── Case2_Static_Actor
│      ├── Script_Code
│      └── Video
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
└── Supplementary_Discussion.pdf
└── README
```


#### 🧪Case Studies - `env-self-driving-car`

> #### ADSHighAggressive
>
>> The system completely disregards emergency braking and adherence to traffic regulations, maintaining a distance of 10 from the preceding vehicle.
>>
>> **Model**: `ADSHighAggressive.aadl`
>>
>> **Generated Automata**: `ADSHighAggressiveProduct.xml`
>
> ---
>
> #### ADSLowAggressive
>
>> The system considers emergency braking and adherence to traffic regulations, decelerating at a distance of 30 from the preceding vehicle. The system is refined by optimizing acceleration and deceleration controls.
>>
>> **Model**: `ADSLowAggressive.aadl`
>>
>> **Generated Automata**: `ADSLowAggressiveProduct.xml`



#### 🔁 CARLA-based Reproduction

We reproduce unsafe scenarios in CARLA by injecting counterexample traces generated from **EnvAADL** models. Each case includes environmental parameters (e.g., friction), environmental actors, and initial system states.

- Case1: Random Actor
- <img src="README.source/carla1.png" alt="carla1" style="zoom:66%;" />
- Case2: Static Actor
- <img src="README.source/carla2.png" alt="carla2" style="zoom:66%;" />
 
### 🧠 Knowledge Graph Construction
The Knowledge Graph (KG) serves as a reusable knowledge base for SOTIF analysis, capturing causal relationships from potential losses, hazards, unsafe constraints, system actions to environmental conditions. The construction pipeline is made explicit through (i) a step-by-step construction procedure, (ii) a worked example mapping losses and hazards to concrete KG nodes, edges, and properties, and (iii) tooling and reproducibility.  

#### Construction Process: Step-by-Step Procedure.
The KG is designed as a reusable knowledge base for SOTIF analysis, rather than being tailored to a specific ADS. Its construction can be regarded as a systematic, top-down causal reasoning process, informed by traffic accident reports [Sugiyanto, 2017] and scenario modeling standards such as ASAM OpenSCENARIO. The construction steps include:

- **Identify Potential Loss:** Start from high-level `Loss` definitions, e.g., "Loss of life or personal injury."
- **Decompose into Causal Hazards:** Determine system-level hazards that could lead to this loss. For instance, the `Hazard` "vehicle exceeding the speed limit" may result in the `Loss` "Loss of life or personal injury."
- **Formalize Hazards as Constraints:** Translate each hazard into a machine-readable `UnsafeSystemConstraint` node, e.g., "v_ego > vmax."
- **Link Triggering Actions and Environmental Factors:** Identify `Action` nodes (e.g., "acceleration") that can trigger the unsafe constraint, and connect them via `Caused_by` edges. Parameters involved (e.g., `vmax`, represented as `EnvFactorParam`) are influenced by environmental conditions represented by `EnvFactor` nodes (e.g., "Visibility < 50"), forming a structured causal chain from actions to constraints and environmental conditions.

---

#### Example: Hazard-to-KG Mapping.
Building on the reasoning steps described above, we now show how they can be instantiated into concrete nodes and relationships in the Knowledge Graph:

- **Loss Node:** `Loss_ID`: "L-1", `Description`: "Loss of life or personal injury".

- **Hazard Node:** `Hazard_ID`: "H-1", `Description`: "Vehicle exceeding the speed limit", linked to the `Loss` node via a `Caused_by` edge, capturing its causal relation to the potential loss.

- **UnsafeSystemConstraint Node:** `Description`: "v_ego > vmax", linked to the `Hazard` node via a `Caused_by` edge, formalizing the hazard into a machine-readable constraint.

- **Action Node:** `Expression`: "acceleration", linked to the `UnsafeSystemConstraint` node via a `Caused_by` edge, with property `types_of_providing = provide`, indicating that performing this acceleration may lead to exceeding the allowed speed limit.

- **EnvFactor Node:** `Expression`: "Visibility < 50", representing environmental conditions that influence system parameters. The node is constructed with `Type`: "Visibility" and `Expression`: "Visibility < 50".

- **EnvFactorParam Node:** `Expression`: "vmax", `Value`: 20 km/h, `Result`: "minimum", ensuring the strictest safe bound under multiple environmental factors. Linked to the corresponding `EnvFactor` node via an `affect` edge, specifying how low visibility restricts the allowed `vmax`.

Finally, a `Vehicle` node is constructed as the central entity. The previously defined `Loss` nodes are connected to it via `Has` edges, `Action` nodes are connected via `Has` edges, and `EnvFactor` nodes are linked via `In` edges. By centering the `Vehicle` node, the KG enables hierarchical reasoning for SOTIF assessment, beginning with its `Loss` nodes and proceeding through the corresponding unsafe constraints, actions, and environmental factors.

This example demonstrates how a loss is decomposed into hazards, unsafe constraints, actions, and environmental factors, producing a structured causal subgraph that is queryable in the KG.

---

#### Automation Level, Tooling and Reproducibility. 
The current KG construction is performed **manually**, but it follows a systematic and well-structured process that enables consistent extension to new scenarios. Users can import our existing knowledge graph (released as `neo4j.dump` on the project website) and adapt it to specific SOTIF analysis needs using official [Neo4j queries](https://neo4j.com/deployment-center/#releases). The `SOTIFA` tool can then parse the KG and complete the subsequent SOTIF assessment. To support reproducibility and collaboration, the entire KG dataset and the associated `SOTIFA` plugin are released on the project website. In future work, we aim to develop tools that automatically instantiate constraints from formal ADS specifications, reducing manual effort and accelerating KG construction.

[Sugiyanto, 2017]: Gito Sugiyanto. The cost of traffic accident and equivalent accident number in developing countries (case study in Indonesia). In: ARPN Journal of Engineering and Applied Sciences, Vol. 12, No. 2, 2017, pp. 389–397.



### 🌍 Environmental Factors

**SOTIFA** considers a broad range of environmental factors, including: **road characteristics** (e.g., type, slope, friction), **atmospheric conditions** (e.g., weather, visibility), and **infrastructure elements** (e.g., traffic lights, rail crossings, parking restrictions, and restricted U-turn areas), as well as both dynamic and static actors involved in the scenario.

Constraints such as *traffic light restrictions*, *rail crossing areas*, *parking restrictions*, and *restricted U-turn areas* are primarily represented based on their **spatial extent**. Each is defined as a bounded rectangular region using coordinate parameters (e.g., `parking_restrictionX_env` and `parking_restrictionY_env`), which allows for distance-based constraint representation. In addition to spatial boundaries, dynamic infrastructure states—such as the state of a traffic light—are modeled through variables like `signal`, which encode whether a condition permits passage or not.

Rather than assigning fixed values or simply sampling from a uniform range, SOTIFA uses dynamic expressions such as `slope = [0.4, 0.6]` to indicate the **search bounds for a dynamic input signal**, $slope(t)$. These predefined bounds are passed into the falsification engine, which searches for critical trajectories likely to trigger unsafe control actions.

To enable such trajectory-level analysis, each input signal is parameterized as a piecewise continuous function. The **granularity** of the analysis is directly determined by the number of user-defined interpolation segments (e.g., 3 or 5), which control the signal's complexity. This mechanism enables the falsifier to explore a richer and more nuanced dynamic input space, as opposed to simplistic random sampling strategies.

The implementation relies on the GNU Scientific Library (GSL) [Gough, 2009], allowing efficient numerical computation and optimization. This integration empowers SOTIFA to conduct a more thorough analysis of environmental uncertainty, contributing to more robust SOTIF risk identification.

[Gough, 2009]: Gough, Brian. *GNU Scientific Library Reference Manual*. Network Theory Ltd., 2009.

### 🚀Scalability and Complexity of SOTIFA
We provide a discussion of scalability, computational performance, and potential strategies for managing complexity in industrial-scale autonomous driving systems.

#### Complexity Analysis.
In our work, SOTIF risks are assessed by evaluating ADS behaviors for **each EUCA** derived from the STPA process. This evaluation requires identifying unsafe control actions, which can be formulated as a *reachability problem* in the system's hybrid state space and addressed via *falsification* techniques. To explore the system's complex hybrid state space, we adopt a divide-and-conquer strategy by first decomposing it into individual **mode sequences** and exploring each sequence separately. For the high-dimensional and nonlinear continuous dynamics within a given mode sequence, we then build upon the *classification-based derivative-free optimization (CDFO)* approach [Yu et al., 2016] to efficiently identify potential EUCAs for SOTIF evaluation. CDFO follows an iterative **sampling–evaluation–classification** procedure, where each iteration (or *query*) consists of sampling a candidate solution, evaluating it, and updating the classification model to guide the next optimization iteration. The *query complexity* of CDFO is then defined as the total number of such iterations required to obtain an optimal or approximately optimal solution.  

Therefore, the overall complexity for our SOTIF assessment can be expressed as:
$$O \Big(K \cdot (m_{L})^B \cdot Q \cdot (m+C_k+k)\Big)$$


Here, $$K$$ denotes the number of EUCAs derived from the STPA process. For **each EUCA**, the number of mode sequences to be explored can be bounded by $$O((m_L)^B)$$, where $$m_L$$ denotes the number of modes in the system model and $$B$$ is a constant mode transition bound. Then for **each mode sequence**, the number of optimization iterations required (i.e., query complexity) is $$Q$$, with each iteration incurring a cost of $$O(m+C_k+k)$$. Specifically, in **each iteration**, the computational complexity of the sampling step and the classification step in [Yu et al., 2016] is both $$O(m)$$, where $$m = m_{X} + m_{U}$$ denotes the number of system variables and external inputs; the computational complexity of the *evaluation step* is $$O(C_k+k)$$, dominated by system trajectory simulation cost $$O(C_k)$$, where $$k$$, $$C_k$$ denote the trajectory bound and the related ODE-solving cost, respectively.  
Besides, regarding the *query complexity* $$Q$$ —defined as the upper bound on the number of iterations required to obtain an $$\epsilon$$-approximate optimal solution with probability at least $$(1-\delta)$$—we refer to the explicit bound established in [Yu et al., 2016]. In particular, under the Lipschitz continuity condition with $$\theta_f = \Big(\tfrac{1}{\beta_1}, \beta_2, \ln L_1, \ln \tfrac{1}{L_2}\Big)$$ denoting the relevant Lipschitz parameters, it holds that $$Q=O \Big({poly}\left(\tfrac{1}{\epsilon}, m, \theta_f \right)\cdot \ln \tfrac{1}{\delta}\Big)$$, which is polynomial in $$m$$.  

#### Scalability Limits and Performance Considerations.  
According to above analysis, as the system scales, several factors contribute to an increase in computational cost. First, the number of system variables and external inputs, $$m = m_{X} + m_{U}$$, generally grows, which increases both the query complexity $$Q$$ (polynomially) and the cost of each optimization iteration. Second, larger systems typically involve more controllers, resulting in more system modes $$m_L$$, and thereby exponentially increasing the number of mode sequences $$(m_L)^B$$. Lastly, the total number of candidate EUCAs $$K$$ may also grow with the system scale due to combinatorial interactions among controllers and environmental factors, further linearly increasing the overall cost.  

To mitigate this complexity growth, `SOTIFA` incorporates several practical strategies. First, combinatorial testing is employed to systematically reduce the number of EUCA combinations, avoiding the need for exhaustive enumeration. Second, domain knowledge encoded in our constructed knowledge graph (Algorithm 1) is leveraged for pruning: for example, the `Caused_by` relation allows us to exclude logically inconsistent pairs such as `not provide acceleration` when the USC is `v > vmax`. Besides, falsification terminates once an unsafe action is detected, avoiding unnecessary simulations and reducing practical computational cost.  

Together, these mechanisms substantially reduce the number of EUCAs and practical runtime cost. As a result, although the theoretical worst-case complexity grows with the number of EUCAs, system variables, external inputs and modes, our observed runtime remains manageable in practice.  

#### Modular Analysis and Abstraction.
Evaluating industrial-scale ADSs is challenging because the system model typically involves behaviors of multiple vehicle components and complex controllers, resulting in a large number of variables, control modes and mode transitions, and consequently high computational complexity for SOTIF assessment. In our future work, a potential solution to this challenge is to adopt modular analysis. In our approach, fortunately, each EUCA focuses on the specific subset of the system pertinent to the corresponding unsafe action and its environmental context, which may enable scenario-specific modular analysis and abstraction and potentially facilitate scalable ADS SOTIF assessment.  

For example, in future work, when conducting more detailed analyses of multi-vehicle scenarios, vehicles with little impact on the current EUCA could be pre-analyzed to reduce computational cost, with their behavior abstracted as hyperrectangles or time-varying sets.  
Similarly, at the control level, irrelevant control modes and switching rules within ADS's complex control logic could also be aggregated or pruned to obtain an abstract representation of the system behavior when analyzing a specific EUCA (e.g., when considering control logic in highway driving or urban autonomous parking scenarios). Such modular decomposition and abstraction could substantially reduce the number of variables, modes, and dimensions, thereby lowering the overall analysis complexity.


[Yu et al., 2016]: Yang Yu, Hong Qian, and Yi-Qi Hu. *Derivative-free optimization via classification*. In: Proceedings of the AAAI Conference on Artificial Intelligence, Vol. 30, No. 1. 2016.


### 📊 Statistical Significance and Sensitivity Analysis

We conducted 15 independent runs per configuration (TB1–TB4, IDM1–IDM4, OVM1–OVM4) to assess risk. Wilcoxon signed-rank tests show significant differences (p < 0.05) across all model pairs. Bootstrap analysis provides mean risk scores and 95% confidence intervals.

### Table: Statistical Comparison of Risk Scores

| **Model ID** | **Mean (95% CI)**                  | **Significance ($p$)**      |
|--------------|------------------------------------|------------------------------|
| TB1          | 0.679635 (0.679085, 0.680160)      | vs TB2–4: < 0.05             |
| TB2          | 0.382802 (0.382654, 0.382951)      | vs TB1,3,4: < 0.05           |
| TB3          | 0.697054 (0.696816, 0.697323)      | vs TB1,2,4: < 0.05           |
| TB4          | 0.518920 (0.518791, 0.519054)      | vs TB1–3: < 0.05             |
| IDM1         | 0.382099 (0.381824, 0.382391)      | vs IDM2–4: < 0.05            |
| IDM2         | 0.423404 (0.423340, 0.423470)      | vs IDM1,3,4: < 0.05          |
| IDM3         | 0.393224 (0.393099, 0.393360)      | vs IDM1,2,4: < 0.05          |
| IDM4         | 0.402253 (0.402144, 0.402375)      | vs IDM1–3: < 0.05            |
| OVM1         | 0.389187 (0.389053, 0.389333)      | vs OVM2–4: < 0.05            |
| OVM2         | 0.494473 (0.494357, 0.494583)      | vs OVM1,3,4: < 0.05          |
| OVM3         | 0.472183 (0.471796, 0.472538)      | vs OVM1,2,4: < 0.05          |
| OVM4         | 0.422130 (0.421958, 0.422319)      | vs OVM1–3: < 0.05            |


### ⚙️ Sensitivity of SOTIFA Formula

Three parameters involved in  **EUCA Risk Value (ERV)** 
Here, the parameters are defined as:

- `k₁ = 1.57` (approximation of π/2 for tangent)
- `k₂ = 1.5`
- `k₃ = 10`

We apply ±20% variation to test the robustness of the formula across four ADS configurations (TB1–TB4).

##### 🔬 Sensitivity Results

| **k₁** | **k₂** | **k₃** | **TB1**   | **TB2**   | **TB3**   | **TB4**   |
|--------|--------|--------|-----------|-----------|-----------|-----------|
| 1.57   | 1.5    | 10     | 0.679635  | 0.382802  | 0.697054  | 0.518920  |
| 1.30   | 1.5    | 10     | 0.682470  | 0.384439  | 0.702480  | 0.526112  |
| 1.57   | 1.3    | 10     | 0.677391  | 0.379611  | 0.696454  | 0.516535  |
| 1.57   | 1.5    | 8      | 0.675791  | 0.376590  | 0.691530  | 0.513414  |
| 1.57   | 1.7    | 12     | 0.680553  | 0.385474  | 0.699097  | 0.520160  |

The SOTIFA scores remain stable under moderate parameter changes, showing robustness in identifying high-risk ADS configurations.


### 🔒 Probabilistic Guarantees

Our choice of falsification stems from the inherent undecidability of verifying complex hybrid systems that combine continuous dynamics with discrete logic. Instead, we focus on falsification-guided testing as a scalable and practical approach to finding safety violations. While falsification-based evaluation by its nature cannot guarantee completeness, our approach proposes the ***EUCA Risk Value (ERV)*** to provide a reference value for the SOTIF-related risk based on the falsification process.

Although the ERV does not provide formal guarantees of completeness, our method's underlying falsification is built upon a well-established theoretical foundation in classification-based derivative-free optimization, as described by [Yu et al., 2016]. This foundation provides probabilistic guarantees on its ability to approximate the global optimum within a bounded number of queries.

Specifically, given an objective function \(f\), if a classification-based optimization algorithm has failure probability \(\delta > 0\) and approximation level \(\epsilon \geq 0\), the query complexity (i.e., the number of solution samples) is upper bounded by:

$$
\mathcal{O}\left(\frac{1}{|D_\epsilon|} \left((1 - \lambda) + \frac{\lambda}{\gamma T} \sum_{t=1}^T \frac{1 - \frac{R_t}{1 - \lambda} - \theta}{|D_t|} \right)^{-1} \ln \frac{1}{\delta}\right)
$$

This implies that the probability of obtaining a solution satisfying \( |f(x) - f^{\text{opt}}| \leq \epsilon \) is at least \(1 - \delta\), i.e.,

$$
\mathbb{P}(| f(x) - f^{\text{opt}} | \leq \epsilon) \geq 1 - \delta 
$$

where:

- $f^{\text{opt}}$ is the minimum function value  
- $D_{\epsilon}$ is the area of the overall target solutions (i.e., solutions close to the global optimum within $\epsilon$)  
- $D_t$ is the area of the target solutions in iteration $t$ (i.e., the area that $\tilde{D}_t$ approximates)  
- $|\cdot|$ denotes the ratio of the area to the total search space  
- $R_t$ is the prediction error of $\tilde{D}_t$ with respect to $D_t$  
- $T$ is the total number of iterations


Importantly, while our system is not formally verified, this theoretical result ensures that, under reasonable conditions on the learning model (i.e., small $\theta$-dependence and $\gamma$-shrinkage), our sampling procedure is not arbitrary and will identify unsafe behaviors with high probability if they exist within the accessible search space. In practice, we have demonstrated this capability in ADS, exhibiting continuous behavior in a complex and uncertain environment.


[Yu et al., 2016]: Yang Yu, Hong Qian, and Yi-Qi Hu. *Derivative-free optimization via classification*. In: Proceedings of the AAAI Conference on Artificial Intelligence, Vol. 30, No. 1. 2016.



### SOTIFATools

- `SOTIFASite`: SOTIFASite plug-in files can be installed.  
- `lib`: The required libraries of the assessment.  
- `neo4j dump`: The knowledge graph.

### Additional Resources

- Installation and usage videos are available:  
  - `SOTIFA Installation.mp4`  
  - `SOTIFA Usage.mp4`  
