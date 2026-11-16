# Medivale Family Medicine

## 16D. Clinical Evidence and Statistics

The worked examples use hypothetical populations to illustrate statistical principles.

### Start with a clinical question and an outcome that matters

Define population, intervention or exposure, comparison, and outcome. Distinguish symptom relief or biomarker improvement from hospitalization or survival benefit. Judge applicability from participants, comparator, follow-up, treatment burden, clinical context, and patient goals.

Risk over a period, rate per person-time, continuous measurement, and time to an event are different quantities. Check denominator, event definition, and time horizon before comparing results.

### Test characteristics condition on different groups

Sensitivity asks how often a test is positive **among people with the condition**. Specificity asks how often it is negative **among people without the condition**. Positive predictive value asks how often the condition is present **among positive results**; negative predictive value asks how often it is absent **among negative results**. Switching those denominators produces a different answer. [CDC test-performance definitions](https://archive.cdc.gov/www_cdc_gov/csels/dsepd/ss1978/lesson5/appendixa.html)

**Test-performance example.** In 1,000 people, 100 have a condition. A test is positive in 90 of those 100 and negative in 720 of the 900 without the condition:

| Result | Condition present | Condition absent |
| --- | --- | --- |
| Positive | 90 true positives | 180 false positives |
| Negative | 10 false negatives | 720 true negatives |
| Total | 100 | 900 |

| Measure | Calculation in this example |
| --- | --- |
| Sensitivity | 90 / 100 = 90% |
| Specificity | 720 / 900 = 80% |
| Positive predictive value | 90 / 270 = 33.3% |
| Negative predictive value | 720 / 730 = 98.6% |

Most positive results in this example are false positives despite high sensitivity. That is not an arithmetic contradiction: there are many more people without the condition available to generate false positives. The false-negative fraction among people with the condition is 10%; the false-positive fraction among those without it is 20%. Neither uses all test results as its denominator. Predictive values depend on the tested population. For a fixed sensitivity and specificity, lower prevalence decreases positive predictive value. In practice, test performance itself may also differ with the population, threshold, and disease spectrum, so values from one setting are not automatically transferable.

### Likelihood ratios update odds, not probabilities directly

For a binary test, **LR+ = sensitivity / (1 - specificity)** and **LR- = (1 - sensitivity) / specificity**. Convert pretest probability to odds, multiply by the applicable likelihood ratio, and convert back: odds = probability / (1 - probability); probability = odds / (1 + odds). An LR of 1 leaves odds unchanged. A result does not become definitive solely because a mnemonic labels a test sensitive or specific. [Oxford CEBM likelihood ratios](https://www.cebm.ox.ac.uk/resources/ebm-tools/likelihood-ratios)

In the worked example, LR+ is **4.5** and LR- is **0.125**. At a 10% pretest probability, the pretest odds are 1/9. After a positive result, odds become 0.5, corresponding to **33.3%** probability. After a negative result, odds become 1/72, corresponding to **1.37%** probability. The negative-result disease probability is the complement of the negative predictive value above.

With the same likelihood ratios and a **20%** pretest probability, pretest odds are 0.25. Positive-result odds become 1.125, giving **52.9%** probability; negative-result odds become 0.03125, giving **3.03%** probability. The same test result leaves different residual risk at a different starting probability.

Whether a remaining probability is acceptable depends on the consequences of missing disease, the risks of further testing or treatment, and the clinical decision threshold. Repeated tests that measure closely related information may not supply independent evidence; multiplying their likelihood ratios without a valid model can exaggerate certainty. A result should change a management decision, not merely add another label to the chart.

### Absolute benefit is not the same as relative benefit

Risk is the proportion experiencing an event during a defined period. For an undesirable outcome, **absolute risk reduction** is control risk minus intervention risk; **relative risk** is intervention risk divided by control risk; **relative risk reduction** is 1 minus relative risk. A relative reduction needs the baseline risk to communicate absolute benefit. [CDC measures of association](https://archive.cdc.gov/www_cdc_gov/csels/dsepd/ss1978/lesson3/section5.html)

**Treatment-effect example.** Over two years, 120 of 1,000 control participants and 80 of 1,000 intervention participants experience an event. Control risk is 12%, intervention risk is 8%, absolute reduction is **4 percentage points**, and relative reduction is **33.3%**. The point-estimate **number needed to treat is 25 over two years**, calculated as 1 / 0.04. This is an average effect, not a guarantee of benefit for an identifiable individual.

If an unwanted effect occurs in 5% with intervention and 3% with control over that period, absolute increase is 2 percentage points and the point-estimate **number needed to harm is 50**. Benefit and harm must refer to their actual outcomes and follow-up. Their NNT and NNH cannot be compared as if all outcomes have equal severity. NNT also varies with baseline risk and uncertainty in the underlying effect. [Cochrane interpreting absolute effects](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-15)

If the same relative reduction applies at a 3% baseline risk, intervention risk would be 2%, absolute reduction 1 percentage point, and NNT 100 for the same period. This extrapolation depends on a transferable relative effect; the arithmetic alone does not establish applicability.

### Read the effect measure before interpreting the estimate

**Odds** are probability divided by one minus probability. An odds ratio compares odds, not risks. In the two-year example, the odds ratio is approximately **0.638**, while the risk ratio is **0.667**; they are not identical. Odds ratios approximate risk ratios when the relevant event risks are low, but that approximation should not be assumed for common outcomes. [CDC risk and odds ratios](https://archive.cdc.gov/www_cdc_gov/csels/dsepd/ss1978/lesson3/section5.html)

A **hazard ratio** compares instantaneous event hazards in a time-to-event analysis; it is not a direct ratio of cumulative risks at a particular date. A mean difference retains an outcome's units, whereas a standardized mean difference expresses an effect relative to variability. For ratio measures, 1 is the usual no-difference value; for difference measures, it is 0. Direction of benefit depends on the outcome and which group is the numerator. [Cochrane effect measures](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-06)

Before using an effect clinically, ask what event was counted, whether the outcome was patient-important or a surrogate, and whether a composite was driven by its least important component. Do not convert an association into a treatment effect simply because it is reported as a precise ratio.

### Match study design to what it can establish

In a randomized trial, assignment is controlled by a random process. In a cohort study, groups are followed from exposure or another defined starting point to outcomes, prospectively or through existing records. A case-control study selects people by outcome status and compares prior exposures. A cross-sectional study measures exposure and outcome at a point or period and often cannot establish which came first. Case reports and series can identify signals but lack a comparison group for estimating a treatment effect. [CDC analytic study designs](https://archive.cdc.gov/www_cdc_gov/csels/dsepd/ss1978/lesson1/section7.html)

Random assignment is not the same as random sampling from the population. It helps create comparable treatment groups on average, but does not guarantee that the study applies to every patient. A case-control sample ordinarily does not supply the population risks needed for a direct risk-ratio calculation because the numbers of cases and controls were selected by design. Check the actual design rather than assuming that the word retrospective means case-control.

**Confounding** occurs when another factor distorts the exposure-outcome association; consider whether it is related to both and whether it is a mediator rather than a confounder. **Effect modification** means an effect differs across a characteristic and can be clinically meaningful rather than an error to remove. An apparent subgroup benefit requires careful examination of design, prespecification, uncertainty, and interaction, not just significance in one subgroup but not another.

**Example.** Patients receiving intensive treatment have more hospital visits but were sicker at baseline. Assess baseline severity, treatment selection, and a suitable comparison before attributing the excess visits to treatment.

### Look for bias in recruitment, measurement, analysis, and reporting

Allocation concealment prevents knowledge of upcoming treatment assignment from influencing enrollment; blinding limits influences after assignment. Intention-to-treat analysis retains participants in their assigned groups to estimate the effect of assignment, but the label does not make missing outcomes harmless. Differential loss to follow-up, unblinded outcome measurement, departures from the intended interventions, and selective result reporting can bias a trial. More participants improve precision; they do not automatically eliminate systematic error. [Cochrane trial risk of bias](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-08)

Selection bias concerns who enters or remains in a comparison; recall or measurement bias concerns how information is obtained. Diagnostic studies can be distorted when only positive tests receive the reference assessment or when the assessor knows the index result. Ask whether the reference standard and recruitment setting fit the intended use. A result in clearly diseased specialist patients versus healthy volunteers may not reflect performance among ambiguous primary care presentations.

A systematic review uses explicit methods to find and appraise evidence; a meta-analysis combines numerical results. Pooling does not cure biased source studies, incompatible populations, or selective publication. Examine the studies contributing weight, their outcome definitions and follow-up, and whether one combined estimate is clinically defensible. A review's title is not itself a quality grade. [Cochrane bias in evidence synthesis](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-07)

Certainty is assessed for an outcome, not awarded to every conclusion in a paper at once. GRADE examines risk of bias, inconsistency, indirectness, imprecision, and publication bias when considering reasons to lower certainty. A large effect estimate and a confident recommendation are not synonyms. Recommendations also consider benefit-harm balance, patient values, resources, and implementation. An estimate from a different population or a surrogate outcome may be indirect even when its arithmetic is precise. [Cochrane evidence certainty](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-14)

### Uncertainty and clinical importance need more than a significance label

A confidence interval describes uncertainty from an estimation procedure under its assumptions. In repeated use of a valid 95% confidence-interval procedure, about 95% of the resulting intervals would cover the fixed parameter. It does not mean that 95% of patients have values inside the interval or that the observed interval assigns a 95% probability to the fixed parameter. Width reflects precision, not protection against every bias. [NIST confidence intervals](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm)

A p-value evaluates incompatibility of observed data, or more extreme data under the specified test, with a statistical model including the null hypothesis. It is **not** the probability that the null hypothesis is true, the probability that the result occurred by chance, or the size of the clinical benefit. Consider the design, estimate, uncertainty, and consequences rather than allowing a threshold alone to determine the conclusion. [ASA statement on p-values](https://www.amstat.org/asa/files/pdfs/P-ValueStatement.pdf)

For a risk ratio of **0.80 with a 95% confidence interval of 0.55-1.15**, the interval includes no effect and also a potentially important benefit and harm. Calling it not statistically significant does not demonstrate equivalence. Conversely, a precisely estimated tiny effect may be statistically significant without being useful to the patient. Noninferiority requires its own justified margin and design, not simply failure to find a difference.

Type I error is rejecting a true null hypothesis; type II error is failing to reject a false one under the specified alternative. Power is 1 minus the type II error probability. Multiple analyses, small samples, missing data, and post hoc choices affect interpretation. A study without enough precision to detect a clinically important difference cannot establish that the treatments are the same. [NIST hypothesis-testing framework](https://www.itl.nist.gov/div898/handbook/prc/section1/prc13.htm)

### Screening outcomes can mislead even when the numbers are correct

Lead-time bias makes survival from diagnosis longer when diagnosis moves earlier without death moving later. Length bias favors detecting conditions with a longer detectable phase. Overdiagnosis identifies disease that would not have caused clinical harm during the person's life; it is not the same as a false-positive test. A screening strategy should be judged by meaningful outcomes and harms rather than the number of diagnoses or survival after diagnosis alone. [NCI screening evidence](https://www.cancer.gov/about-cancer/screening/hp-screening-overview-pdq)

**Lead-time example.** Cancer is diagnosed at 66 rather than 70, while death occurs at 74 in either scenario. Survival after diagnosis changes from four to eight years with no gain in lifespan. Earlier detection helps only when the screening pathway improves meaningful outcomes.

Testing can also initiate a cascade of repeat imaging, invasive procedures, incidental findings, anxiety, and costs. Before testing, specify how either result will change care and whether the full follow-up pathway is feasible. These considerations connect evidence interpretation to the prevention decisions in volumes 1A-1B.

### Quality improvement turns evidence into reliable care

Define a specific aim, choose a change tied to the identified problem, and test it on a small scale. Use repeated **plan-do-study-act** cycles to learn from the result before wider implementation. An intervention that works under one condition should be tested under relevant different conditions. A before-and-after improvement alone does not establish that the change caused it. [IHI improvement framework](https://www.ihi.org/library/model-for-improvement)

| Measure type | Referral-follow-up example |
| --- | --- |
| Process | Proportion of urgent referrals with receipt confirmed by the receiving team. |
| Outcome | Time from an urgent referral to the needed clinical assessment. |
| Balancing | Routine appointment delays or staff burden created by the new workflow. |

Track measures over time and examine whether results differ across groups facing access barriers. A favorable overall average can conceal a group left behind. Measurement should test whether care improved, not reward documentation alone. [IHI outcome, process, and balancing measures](https://www.ihi.org/library/model-for-improvement/establishing-measures)

For population health, distinguish eligible patients, completed services, unresolved abnormal results, and patients not yet reached. Use these denominators to target outreach and measure completed care.
