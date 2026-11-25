# Methods

Each section below belongs to one dashboard page or tab. 

**Approach:** For my own understanding, I wrote an explanation of the basics of each test and method, in the style of "lecture notes". Assumes familiarity with basic Probability, not so much with basic Statistics.

## Overview

**Goal.** Counts for some of the most relevant metrics. 

**Definitions.** Over the $N$ Runs selected, with $y_j = 1$ if Run $j$ was won and $y_j = 0$ if lost:

- *WR (win rate):* The mean $\bar y = \frac{1}{N}\sum_j y_j\in[0,1]$. 
- *Deck size:* Average number of Cards in the deck when the Run ended.
- *WR by Boss* $b$: The mean $\bar y$ but only over the Runs that fought $b$. 
- *Survival rate by Act* $a$: Share of the Runs that reached Act $a$ that did not die in it. 
- *WR by Ancient* $a$: The mean $\bar y$ but only over the Runs that met $a$.
- *WR by Ancient Relic* $r$: The mean $\bar y$ but only over the Runs that took $r$.
- *Card pick rate by Act*: For a pair $(c, a)$ of Card $c$ and Act $a$, the share of the offers of $c$ in $a$ that were picked.
- *Card Act SR (Act survival rate)*: For a pair $(c, a)$, how often picking $c$ in $a$ was followed by surviving $a$.
- *Card Run WR (Run win rate) by Act*: For a pair $(c, a)$, how often picking $c$ in $a$ was followed by winning the Run. **Note:** This is, in general, smaller than the Card Act SR. In the last Act, both coincide.

**What it sees.** Plain frequencies, exactly as they happened.

**What is not seen.** A lot...

## HP lost per Fight type

**Goal.** Quantify HP cost of Normal, Elite and Boss Fights.  

**Data.** Let $D_{jf}$ be the average HP lost on Run $j$ over all Fights of type $f$ (i.e. Normal Fights, Elite Fights or Boss Fights).

For every pair $(f, g)$ of types, with $f$ the "harder" one, let

$$d_j = D_{jf} - D_{jg}$$

for every Run $j$ that saw at least one Fight of each type.

**Why average per Run.** Note that grouping by Run is necessary for the following reasons:

- Fights in a Run are not independent: they share the same deck and Relics (and how well one played at that time). If treated independently, standard errors would be too small and the p-values too optimistic. 
- Less noise: the variance of the difference in $d_j$ is smaller than the sum of individual variances, since HP lost is positively correlated (a weak deck loses HP everywhere).

**Methods.** 

(1) *[Paired $t-$test](https://en.wikipedia.org/wiki/Student%27s_t-test#Paired_samples).* Test $H_0: \mathbb{E}[d_j] = 0$, against $H_1: \mathbb{E}[d_j] \neq 0$.

With

$$\bar d = \frac{1}{N}\sum_j d_j,$$

$$s_d^2 = \frac{1}{N-1}\sum_j (d_j - \bar d)^2,$$

$$\mathrm{SE} = \frac{s_d}{\sqrt N},$$

the test statistic is

$$t = \frac{\bar d}{\mathrm{SE}} \sim t_{N-1} \quad \text{under } H_0.$$

The p-value is the probability, if $H_0$ were true, of a statistic at least as
far from zero as the one observed: 

$$p = \mathbb P\big(|T| \ge |t|\big) = 2\big(1 - F_{N-1}(|t|)\big), \qquad T \sim t_{N-1}.$$

Equivalently, since $H_1$ is two-sided, 

$$p=2(1-F_{N-1}(|t|)),$$

where $F_{N-1}$ is the CDF of $T$ as above. 


The test rejects $H_0$ when $p < 0.05$, which is the same as $|t| > t_{N-1,\,0.975}$.


> *Why this statistic, and why the t distribution.* 
> Suppose $(d_j)_{j=1}^N$ are independent Gaussians with mean $\mu$ and variance $\sigma^2$. Then, the naive test statistic to consider is
>
> $$Z = (\bar d - \mu)/(\sigma/\sqrt N) \sim \mathcal N(0, 1).$$
> 
> Under $H_0$ we assume $\mu=0$, but the key issue is that we still do not know $\sigma^2$. Replacing it by an estimator adds noise, changing the distribution of the test statistic. 
> 
>  A natural next step is to look at the ratio between the sample variance and $\sigma^2$. Then, 
> $$V=\frac{s_d^2}{\sigma^2}=\frac{1}{N-1}\sum_{j=1}^N(z_j-\bar z)^2,$$
> where $z_j=(d_j-\mu)/\sigma$ are independent standard Gaussians. By definition, the sum of $k$ squared independent standard Gaussians is a $\chi_k^2$ random variable. Since everything is fitted to the mean, only $N-1$ terms in the above sum are free, so
> $$(N-1)\,V\sim\chi^2_{N-1}.$$
> Note that this is the precise reason the definition of $s_d^2$ divides by $N-1$ instead of $N$: it is then an unbiased estimator for $\sigma^2$, meaning that $\mathbb{E}[s_d^2]=\sigma^2$. 
>
> The final key observation is that
> $$\frac{Z}{\sqrt{V}}=\frac{\bar d -\mu}{\mathrm{SE}},$$
> so that the unknown $\sigma$ cancels out. By definition, this is a $t_{N-1}$ random variable. Under $H_0$, it is precisely the statistic above.

(2) *The 95% confidence interval.* The 95% CI of the above statistic is

$$\bar d \pm t_{N-1,\,0.975}\cdot \mathrm{SE},$$

where $t_{N-1,\,0.975}$ is the 97.5% quantile of $t_{N-1}$.

In particular, the interval excludes zero when $p<0.05$ in the paired $t-$test. **Note:** This is true for the unadjusted $p-$values, see below.

(3) *[Wilcoxon signed-rank test](https://en.wikipedia.org/wiki/Wilcoxon_signed-rank_test).* Test $H_0$: the law of $d_j$ is symmetric around 0, against $H_1$: it is not. 

We drop Runs with $d_j=0$ and let $N$ be the total number of Runs left. We rank the $|d_j|$ from 1 (smallest) to $N$ (largest). Any ties are given the average of their ranks. The test statistic is

$$W^+ = \sum_{j:\, d_j > 0} \mathrm{rank}(d_j).$$

Note $W^+\in[0,\ N(N+1)/2]$, where the endpoints correspond to all $d_j$ being negative or positive, respectively.

Under $H_0$, 

$$W^+ = \sum_{j=1}^N jB_j, \qquad B_j\sim\textrm{Ber(1/2)}\ \textrm{independent}.$$

So we have that

$$\mathbb{E}[W^+] = \frac{N(N+1)}{4}, \qquad \mathrm{Var}[W^+] = \frac{N(N+1)(2N+1)}{24}.$$

The p-value is the probability, if $H_0$ were true, of a statistic at least as far from
$\mathbb{E}[W^+]$ as the one observed. 

For small samples, this probability is computed explicitly by enumerating all Bernoulli patterns and their respective probabilities (scipy does this up to 50 Runs, or 13 when there are ties or zeros). Otherwise, it uses the Gaussian approximation.

> *What differs from the $t-$test.* First, no assumption of Gaussianity of $d_j$ is made. But more importantly, the *average* difference considered in the $t-$test can be moved by a few disastrous Fights (i.e. this test is about the typical Run). Agreement in significance of both tests means the conclusion does not depend on either view. 

(4) *[Holm adjustment](https://en.wikipedia.org/wiki/Holm%E2%80%93Bonferroni_method).*
Each method in (1) and (3) is used to test **three** different hypotheses, one per unique pair of types (assuming there are enough Runs that had both types). Instead of controlling individual false rejections, our goal is to control the chance of **at least** one false rejection, which is called the [family-wise error rate](https://en.wikipedia.org/wiki/Family-wise_error_rate) (FWER). In particular, we want to keep this under $\alpha=0.05$. The main complication is that our tests are **not** independent, since e.g. Boss - Normal = (Boss - Elite) + (Elite - Normal), meaning that we cannot compute the FWER exactly.

In general, suppose we have a total of $m$ tests with null hypotheses $H_0^{(i)}$ for $i=1,\ldots,m$, and our goal is to make the FWER at most $\alpha$. Without loss of generality, we can take the indexing such that the respective $p-$values are $p^{(1)}\leq\cdots\leq p^{(m)}$. Our new rule is to reject $H_0^{(i)}$ if 
$$p^{(i)}\leq \alpha/(m-i+1),$$
and stop at the first failure. Equivalently, we reject $H_0^{(i)}$ if $\tilde p^{(i)} \le \alpha$, where

$$\tilde p^{(i)} = \max_{k \le i}\ \big(1 \wedge\ (m - k + 1)\, p^{(k)}\big).$$

To see why this works, let $m_0$ be the number of true null hypotheses and let $i\leq m-m_0+1$ be the first true null in the sorted order. By definition, its threshold is $\alpha/(m-i+1)\leq\alpha/m_0$. Since we stop at the first failure, any false rejection requires rejecting this null first, and hence that at least one of the $m_0$ true nulls has $p-$value at most $\alpha/m_0$. The $p-$value of a true null satisfies $\mathbb{P}(p\leq u)\leq u$, so by a union bound this has probability at most $m_0\times\alpha/m_0=\alpha$. 

For our analysis, the $t-$test and Wilcoxon $p-$values are adjusted as two separate families. **Note:** Only $p-$values are adjusted, so a 95% CI can exclude zero while its adjusted $p-$value is above 0.05.

**What is not seen.**

- *Timing.* No reweighting is done according to how early the Normal/Elite Fight is. 
- *Easy Pool of Normal Fights.* On top of the previous item, Normal Fights from the "Easy Pool" are not treated separately.
- *Capped damage.* A fatal Fight costs at most the HP that was left.
- *Weights.* Every Run counts once, however many Fights of each type it had. However, e.g. a Run with more Elite Fights should have less HP cost per Fight (corresponding to a strong Run where taking Elites was comfortable).

## HP lost per turn

**Goal.** Quantify the HP cost of one extra turn in a Fight, separately for Normal, Elite and Boss Fights.

**Data and model.**

*Selection.* A selection is a Fight type (Normal, Elite or Boss) for one fixed Character. Optionally, it may be narrowed to an Act, and further to an individual named Fight of that Act.

Every instance of a valid Fight in the selection (i.e. each data point) is indexed by $i = 1, \ldots, N$. For each $i$, let

- $H_i$ be the HP lost,
- $\tau_i$ be the number of turns taken,
- $A_i$ be the Ascension of its Run,
- $E_i$ be its named Fight (e.g. "Byrdonis").

*Controls.* Let $e_0, e_1, \ldots, e_L$ be the distinct named Fights in the selection, where $e_0$ is the most common one (the *reference*). The *controls* of Fight $i$ are the vector

$$z_i = \big(A_i,\ \mathbf 1\{E_i = e_1\},\ \ldots,\ \mathbf 1\{E_i = e_L\}\big) \in \mathbb R^{1+L}.$$

Note that the Ascension enters as a number and that there is no control for the reference $e_0$. A control that does not vary in the selection is dropped. For instance,
- If the Ascension is fixed (in the Dashboard), then $A_i$ is dropped.
- If an individual named Fight is fixed (so $L=0$), then all indicators of $E_i$ are dropped.
- If both above are fixed, then $z_i$ is empty.

*Model ([linear regression](https://en.wikipedia.org/wiki/Linear_regression)).* We assume

$$H_i = \beta_0 + \beta_1 \tau_i + \gamma^\top z_i + \varepsilon_i, \qquad \mathbb E[\varepsilon_i \mid \tau_i, z_i] = 0,$$

where $\varepsilon_i$ models "everything else" that decides $H_i$ (e.g. the deck, the draws, the Relics). The unkown coefficients to be estimated are $\beta_0, \beta_1 \in \mathbb R$ and

$$\gamma = (\gamma_A,\ \gamma_{e_1},\ \ldots,\ \gamma_{e_L}) \in \mathbb R^{1+L}.$$

Note that, since at most one indicator is non-zero, 

$$\gamma^\top z_i = \gamma_A A_i + \gamma_{E_i}.$$

Moreover, by definition, $\gamma_{e_0} = 0$.

Taking expectations in the model:

$$\mathbb E[H_i \mid \tau_i = t,\ A_i = a,\ E_i = e] = \big(\beta_0 + \gamma_e + \gamma_A a\big) + \beta_1 t.$$

That is, for each value $(a, e)$ of the controls, the expected HP lost is a line in the turns.

*What is $\beta_1$?* By the above equation,  

$$\beta_1 = \mathbb E[H_i \mid \tau_i = t + 1,\ A_i = a,\ E_i = e] - \mathbb E[H_i \mid \tau_i = t,\ A_i = a,\ E_i = e].$$

That is, $\beta_1$ is the expected HP lost per extra turn *across Fights with the same controls*.

*What is $\gamma$?* Similarly, 

$$\gamma_{e_\ell} = \mathbb E[H_i \mid \tau_i = t,\ A_i = a,\ E_i = e_\ell] - \mathbb E[H_i \mid \tau_i = t,\ A_i = a,\ E_i = e_0],$$

$$\gamma_A = \mathbb E[H_i \mid \tau_i = t,\ A_i = a + 1,\ E_i = e] - \mathbb E[H_i \mid \tau_i = t,\ A_i = a,\ E_i = e],$$

That is, $\gamma_{e_\ell}$ is the expected difference of HP loss in $e_\ell$ versus in $e_0$ *across Fights with the same turns and Ascension*. Likewise, $\gamma_A$ is the expected extra HP loss per Ascension *across Fights with the same turns and named Fight*.

> *Why $e_0$ has no indicator.* With one indicator per named Fight the indicators would add up to one. Thus adding any constant to $\beta_0$ and subtracting it from every $\gamma_{e_\ell}$ would give the same model and the coefficients would not be determined.

> *Named Fight as control vs. selection.* Fixing the named Fight as a control means that only comparisons within the same named Fight inform the slope. Consider a simple example of named Fight A and named Fight B with two samples each, given by 
>
> | Named Fight | Turns taken | HP lost |
> |:-:|:-:|:-:|
> | A | 2 | 5 |
> | A | 3 | 7 |
> | B | 6 | 20 |
> | B | 7 | 22 |
>
> Think e.g. that Fight A is an easy Normal Fight while Fight B is a tanky Elite Fight. Our model will estimate $\beta_1=2$  due to the controls, but otherwise it would estimate $\beta_1 = 62/17 \approx 3.6$. Indeed, mixing Fights makes it such that four more turns give, on average, 15 more HP lost. 
> 
> This is **not** the same as selecting a single named Fight $e$ in the Dashboard, which fits the model to $e$ alone. With all named Fights selected, the model assumes they share one slope $\beta_1$ and, since their true individual slopes differ, the estimator is a weighted average of the slopes fitted on each named Fight alone (exactly so when the Ascension is held fixed). Each named Fight weighs in proportion to how often it was fought and how much its length varied (e.g. one that always lasted the same number of turns does not inform $\hat\beta_1$ at all).

**Methods.**

(1) *[Least squares](https://en.wikipedia.org/wiki/Ordinary_least_squares).* Our goal is to estimate the coefficients

$$b = \begin{pmatrix} \beta_0 \\ \beta_1 \\ \gamma \end{pmatrix} \in \mathbb R^k, $$

where $k=2+\dim \gamma$ depends on the number of controls (e.g. $k=3 + L$ when none is dropped). Let $X$ be the $N \times k$ matrix with rows $x_i^\top = (1, \tau_i, z_i^\top)$, let $H = (H_1, \ldots, H_N)^\top$ and let $\varepsilon = (\varepsilon_1, \ldots, \varepsilon_N)^\top$. Our model is then

$$H = Xb + \varepsilon.$$

For any $b'$, we ahve 

$$\mathbb E\big[(H_i - x_i^\top b')^2\big] = \mathbb E[\varepsilon_i^2] + \mathbb E\big[(x_i^\top (b - b'))^2\big].$$

That is, the true $b$ is the one with the smallest second moment. We thus estimate it by minimizing 

$$\sum_{i=1}^N (H_i - x_i^\top b)^2 =: \lVert H - Xb \rVert^2.$$

To find this minimum, note that the expression is a convex quadratic in $b$ and thus has a unique minimizer when its
gradient $-2X^\top (H - Xb)$ is zero. Whenever $X^\top X$ is invertible this gives the unique estimator

$$\hat b = (X^\top X)^{-1} X^\top H.$$

We call $\hat e_i = H_i - x_i^\top \hat b$ the *residuals*. 

(2) *[Cluster-robust standard errors](https://en.wikipedia.org/wiki/Clustered_standard_errors).* To quantify the variance of our estimators, note $\hat b - b = (X^\top X)^{-1} X^\top \varepsilon$ so that

$$\mathrm{Var}(\hat b) = (X^\top X)^{-1}\, X^\top \mathrm{Var}(\varepsilon)\, X\, (X^\top X)^{-1}.$$

Now, the textbook formula assumes independent errors of equal variance, i.e. that $\mathrm{Var}(\varepsilon) = \sigma^2 I$. As in *HP lost per Fight type*, **the problem is that Fights in a Run are not independent**.

To solve this we estimate the block of each Run from its residuals. Namely, let $G$ be the number of Runs in the sample and write $X^{(g)}$, $\varepsilon^{(g)}$ and $\hat e^{(g)}$ for the rows of $X$, the errors and the residuals of the Fights of Run $g$, respectively. Since we assume Runs to be independent, $\mathrm{Var}(\varepsilon)$ is block diagonal with one block $\mathrm{Var}(\varepsilon^{(g)})$ per Run, so

$$\mathrm{Var}(\hat b) = (X^\top X)^{-1}\Big(\sum_{g=1}^{G} X^{(g)\top}\, \mathrm{Var}(\varepsilon^{(g)})\, X^{(g)}\Big)(X^\top X)^{-1}.$$

Writing $u_g = X^{(g)\top}\varepsilon^{(g)}$, each term in the sum is simply $\mathbb E\big[u_g u_g^\top\big]$. 

To estimate it we replace the errors by the residuals, i.e. each $u_g$ by $\hat u_g = X^{(g)\top}\hat e^{(g)}$. As before, since $\hat b$ was fitted to the data, the residuals are smaller than the errors and we must quantify this understatement. We split it into two contributions:

- *Fights.* The residuals are $\hat e = M\varepsilon$, where $M = I - X(X^\top X)^{-1}X^\top$ is symmetric and $M^2 = M$. In the textbook case $\mathrm{Var}(\varepsilon) = \sigma^2 I$,

  $$\mathbb E\Big[\sum_{i=1}^N \hat e_i^2\Big] = \mathbb E\big[\varepsilon^\top M \varepsilon\big] = \mathrm{tr}(M)\sigma^2 = (N - k)\,\sigma^2,$$

  while 
  $$\mathbb E\big[\sum_i \varepsilon_i^2\big] = N\sigma^2.$$
  So the residuals understate the errors by a factor $(N-k)/N$. 
- *Runs.*  By (1), we know that $\hat u_g$ add up to $X^\top \hat e = 0$. Roughly, one should think as if $\hat u_g = u_g - \bar u$. If every $u_g$ had the same variance $s^2$, then

  $$\mathbb E\Big[\sum_{g=1}^G (u_g - \bar u)(u_g - \bar u)^\top\Big] = \sum_{g=1}^G \mathbb E\big[u_g u_g^\top\big] - G\,\mathbb E\big[\bar u \bar u^\top\big] = (G - 1)\,s^2,$$
  while 
  $$\mathbb E\Big[\sum_{g=1}^Gu_g^2\Big] = Gs^2.$$
  So, similarly to before, the residuals (per Run block) understate the errors (per Run block) it by a factor $(G-1)$.

As the two corrections overlap on one degree of freedom,

$$\widehat V = \frac{G}{G-1}\,\frac{N-1}{N-k}\,(X^\top X)^{-1}\Big(\sum_{g=1}^{G} \hat u_g \hat u_g^\top\Big)(X^\top X)^{-1},$$

(3) *Test and 95% CI for $\beta_1$.* We test $H_0: \beta_1 = 0$, against $H_1: \beta_1 \neq 0$. The test statistic is

$$t = \frac{\hat\beta_1}{\mathrm{SE}(\hat\beta_1)}.$$

If $\hat\beta_1$ were Gaussian and $\mathrm{SE}(\hat\beta_1)$ an independent (scaled) $\chi_{G-1}^2$, a similar computation as in *HP lost per Fight type* would give that $t\sim t_{G-1}$ under $H_0$. Neither of these assumptions is true, but for large sample sizes the CLT ensures it holds *approximately*.  

The $p-$value is defined as previously, i.e.

$$p = \mathbb P\big(|T| \ge |t|\big) = 2\big(1 - F_{G-1}(|t|)\big), \qquad T \sim t_{G-1},$$

And the 95% CI is, again, given by

$$\hat\beta_1 \pm t_{G-1,\,0.975}\cdot\mathrm{SE}(\hat\beta_1).$$

(4) *[Coefficient of determination](https://en.wikipedia.org/wiki/Coefficient_of_determination).* To measure how much of the variation in HP lost is explained by the model, we look at

$$R^2 = 1 - \frac{\sum_{i=1}^N \hat e_i^2}{\sum_{i=1}^N (H_i - \bar H)^2}.$$

If $R^2$ is close to $1$, then the HP lost is well-explained by the model. 

**Exceptions to fitting** 

A fitting is skipped if (i) there are fewer than 5 Runs (ii) there are more coefficients than Fights (iii) every Fight had the same HP loss (iv) a column of $X$ is determined by the others 
(e.g. every named Fight lasting a single number of turns).

**What is not seen.**

- *Cause and effect.*  A Fight may last long because the deck is slow or the draws are poor, but those also decide the HP lost. 
- *The Run's state.* HP, deck strength and Relics at the Fight are not in the model.
- *The usual assumptions of a linear regression.* How each fares here:
  - *Linearity.*
  This can fail as some Fights might scale faster (e.g. "Byrdonis").
  - *Independent Runs.* Assumed only for the standard errors in (2). It can fail mildly, e.g. as the player improves or the patch changes.
  - *Equal variance of the errors.* Assumed only for the variance estimate in (2). It likely fails as HP lost varies more in some named Fights than in others.
  - *Gaussian errors.*  Assumed only in (3). It likely fails since HP lost is an integer, never negative and capped at the HP left in a fatal Fight. This is not a problem for large samples by the CLT.
  - *No column of $X$ determined by the others.* Fit is skipped if so. It corresponds to the invertibility assumption in (1).

## Ancient Relics

**Goal.** Quantify, for each Ancient, how likely each of its Relics is to beat the Ancient's average win-rate (WR), and to be its best Relic.

**Data.** For each Relic $r$ of Ancient $a$, let $n_r$ be the number of Runs that took it and $k_r$ the number of those that won. Set $N_a = \sum_r n_r$ and $W_a = \sum_r k_r$. 

**Methods.**

(1) *Model.* Let $\theta_r$ be the true WR of Relic $r$, i.e. the probability that a Run taking it wins. Our goal is the *posterior* law of $\theta_r$, which we derive from a *prior* law combined with the *likelihood* of the observed wins given the prior. 

- *Prior.* Assume $\theta_r \sim \mathrm{Uniform}(0, 1)$. 
- *Likelihood.* Given $\theta_r$, the $n_r$ Runs are independent coin flips with success probability $\theta_r$. So
$k_r \mid \theta_r \sim \mathrm{Binomial}(n_r, \theta_r)$.
- *Posterior.* By Bayes' rule, the density of $\theta_r | k_r$ is proportional to the likelihood times the prior. Here, this density is 
  $$\propto\ \theta_r^{k_r}(1-\theta_r)^{n_r - k_r}.$$
  Equivalently, 

    $$\theta_r \mid k_r \sim \mathrm{Beta}(k_r + 1,\ n_r - k_r + 1),$$
    which has mean

    $$\mathbb{E}[\theta_r \mid k_r] = \frac{k_r + 1}{n_r + 2}.$$

(2) *The Ancient's WR.* To say whether a Relic beats its Ancient, we need a reference WR for the Ancient $a$ itself. A natural/sensible choice is to take the posterior mean in (1) but now overall the Relics of $$. That is, 

$$\mu_a = \frac{W_a + 1}{N_a + 2}.$$

(3) *Outputs.* The probabilities we care about are read off the posterior of each Relic, in the following way:

- *Estimate and [credible interval](https://en.wikipedia.org/wiki/Credible_interval).* To give a value and a range for $\theta_r$ we take the posterior mean and the interval around it from the 2.5% to the 97.5% quantile.
- *Beating the Ancient.* To quantify how likely the Relic is to beat its Ancient's WR, we compute $\mathbb{P}(\theta_r > \mu_a \mid k_r) = 1 - F_r(\mu_a)$ where $F_r$ is the CDF of the posterior.
- *Being the best.* To quantify how likely the Relic is to be the best of its Ancient, we want the probability that it has the highest true WR. Since this has no closed form we use [Monte Carlo](https://en.wikipedia.org/wiki/Monte_Carlo_method): draw many independent samples from the posterior laws of each Relic and approximate the true probabilities by the sampled frequencies.

> *Credible vs. confidence interval.* A *confidence* interval is a statement about a procedure over repeated samples, while a *credible* interval gives a probability concerning $\theta_r$ itself. Similarly, the probability in the second item is not a $p-$value computed assuming a hypothesis is true: it is the probability of the claim itself.

> **TODO.** Above, each Relic gets its *own* uniform prior, so its estimate only uses its *own* Runs regardless of how the other Relics did. A [hierarchical model](https://en.wikipedia.org/wiki/Bayesian_hierarchical_modeling) would replace the uniform prior with a second layer: the true WRs of all the Relics of an Ancient come from a common law, whose mean and variance are learned from *all* the Runs. A Relic with few Runs would then be pulled toward its Ancient's avererage while one with many Runs would keep close to its own WR. This would help a lot with small samples (e.g. when filtering by patch).

**What is not seen.**

-  *Relics are not pooled across each other's performance* See the TODO above.
- *The uncertainty in $\mu_a$.* Here we treat it as a fixed number.

## Card Ratings

**Goal.** Rate each Card of a Character in different ways. Some may depend on only the Card's performance (like win-rate) while others may depend only on the player's preferences (like ELO). 

### Win-rate (WR)

**Data.** For simplicity, we consider only Cards picked in a Fight's rewards, where exactly three Cards are offered (i.e we leave out other rewards from Events, Acients or Shops).

Recall $y_j = 1$ if Run $j$ was won and $y_j = 0$ if it was lost. 

**Definition.** For a Card $c$, let $J_c$ be the Runs that picked $c$ at least once, $n_c = |J_c|$ be the number of such Runs, and $k_c = \sum_{j \in J_c} y_j$ be the number of won Runs among them. 


The natural first measure is the raw WR given by $k_c/n_c$. However, a Card picked on floor $f$ comes from a Run that survived up to floor $f$, and such Runs win more often regardless of what they picked. Thus the raw WR favors Cards picked late ([survivorship bias](https://en.wikipedia.org/wiki/Survivorship_bias)), and one should instead compare only with the Runs that got as far. 

With $F_j$ the last floor of Run $j$, the WR of the Runs that got past floor $f$ is

$$w(f) = \frac{\sum_j y_j\, \mathbf{1}[F_j > f]}{\sum_j \mathbf{1}[F_j > f]},$$

Let $f_{jc}$ be the floor of the first pick of Card $c$ in Run $j$. The expected WR of $c$ read from the floors alone is

$$e_c = \frac{1}{n_c}\sum_{j \in J_c} w(f_{jc}).$$

The natural comparison is against the raw WR of the card, so we look at

$$a_c = \frac{k_c}{n_c} - e_c,$$

such that $a_c > 0$ means the Runs that picked $c$ won more often than Runs that got as far.

> **TODO.** Implement *wins above replacement (WAR)*. This metric compares the WR of the Runs that took a Card with that of the Runs that passed it, measuring the *impact* a Card has on a Run (whether positive or negative).

**What is not seen.**

- *Context* Only the floor is adjusted for. Important states such as HP, deck and Relics at the pick are not. Thus WR measures Cards in a vacuum, irrespective of sinergies anywhere else in the Run.
- *Credit.* Similarly, the outcome of a Run is credited in full to every Card it picked. A particular Card's pick might have been "correct" and the Run lost elsewhere.

### ELO

**Data.** Again, we consider only Cards picked at a Fight's rewards. 
Reward $r$ offers $O_r = \lbrace c_1, c_2, c_3, \mathrm{Skip}\rbrace$ and the player picks $w_r \in O_r$.

**Methods** ([Bradley–Terry](https://en.wikipedia.org/wiki/Bradley%E2%80%93Terry_model)).

To quantify preferences, we give each option $o$ a rating $R_o$ and model that option $a$ is picked over option $b$ with probability 
$$P(R_a > R_b) = \frac{1}{1 + 10^{(R_b - R_a)/400}} = \frac{Q_a}{Q_a + Q_b}, \qquad\text{with}\ \  Q_o = 10^{R_o/400}.$$

In particular, only differences between ratings matter. 

In a "game" between options $a$ and $b$, write $S_a$ for the *score* of $a$. That is, $S_a=1$ if $a$ is picked over $b$ and  $S_a=0$ otherwise. Then $E_a:= P(R_a > R_b)$ can be read as its *expected score* and the [odds](https://en.wikipedia.org/wiki/Odds) of $a$ being picked over $b$ are

$$\frac{E_a}{E_b} = \frac{Q_a}{Q_b} = 10^{(R_a - R_b)/400}.$$

That is, a 400 rating difference corresponds to 10:1 odds. The base 10 and the scaling factor 400 are chess conventions. 

For us, a reward is read as three games: the pick $w_r$ beats each other option of $O_r$. Moreover, each starting rating is set to 1500 (again following chess conventions).

*Updates/Fitting.* The ratings are the parameters of the model and we must adjust them as picks are observed. The goal is to reach an "equilibrium" in which the ratings make the observed picks as likely as possible.

To make this precise, treat the games as independent given the ratings, so that the probability of all the observed picks is 

$$\prod_{\text{rewards}\ r}\ \prod_{o\in O_r,\ o\neq w_r}P(R_{w_r} > R_o).$$

Maximizing this probability is equivalent to minimizing the [log-loss](https://en.wikipedia.org/wiki/Cross-entropy#Cross-entropy_loss_function_and_logistic_regression) given by

$$\mathcal L = \sum_r \mathcal L_r, \qquad \mathcal L_r = -\sum_{o \in O_r,\ o \neq w_r} \log P(R_{w_r} > R_o).$$

Both $\mathcal L$ and each $\mathcal L_r$ are functions of the vector $R = (R_o)_{o \in \mathcal O}$ of ratings, where $\mathcal O$ is the set of all the possible offers. The gradient of $\mathcal L$ is the vector $\nabla \mathcal L = \big(\partial \mathcal L / \partial R_o\big)_{o \in \mathcal O}$.

To compute this gradient, let $\sigma(x) = 1/(1 + 10^{-x/400})$ be the [logistic function](https://en.wikipedia.org/wiki/Logistic_function) in base 10, and note that

$$\frac{d}{dx} \log \sigma(x) = \frac{\log 10}{400}\,\big(1 - \sigma(x)\big).$$

Since $E_a= \sigma(R_a - R_b)$ and $E_b = \sigma(R_b-R_a)=1-\sigma(R_a-R_b)$,

$$\frac{\partial}{\partial R_a}\big(S_a \log E_a + S_b \log E_b\big) = \frac{\log 10}{400}(S_a - E_a),$$

and similarly for $b$. The gradient of $\mathcal L$ is then

$$\frac{\partial \mathcal L}{\partial R_o} = -\frac{\log 10}{400} \sum_{\text{games of } o} \big(S_o - E_o\big),$$

where the sum runs over the games of $o$ *across all rewards*: three for each reward where $o$ was picked and one (against the pick) for each reward where it was not.

The key upshot is to note that the log-loss gradient is zero if and only if every option has scored exactly as many points as the ratings expected it to. This means that an option that scored more than expected is rated too low and should be raised. The natural choice is to move all ratings *some small step* in the direction of $-\nabla\mathcal{L}$ (along with log-loss decreases the fastest). Moreover, the size of the step should be proportional to how far it scores from its expected score.

Standard [gradient descent](https://en.wikipedia.org/wiki/Gradient_descent) would repeatedly take the step $R \leftarrow R - \eta\,\nabla \mathcal L$ of size $\eta$. This has two problems:

- *Every reward weighs the same.* Since $\mathcal L$ is a sum over the whole history, the optimization is done for the player's preferences over *all their Runs*, not their current one. In particular, it does *not* reflect the player's preference over time. 
- *The minimizer may not exist.* If an option won every game it was in, then $S_o - E_o > 0$ in all its games, so $\partial \mathcal L / \partial R_o$ never vanishes and its $R_o$ is pushed to infinity. Similarly, an option that lost every game has its rating puhsed to negative infinity.

Instead, we go through the rewards in *chronological order* (Run start time, then floor) and our update step is $R \leftarrow R - \eta\,\nabla \mathcal L_r$ (i.e. the gradient is zero on the options outside $O_r$, whose ratings do not change, and we move the four ratings of $O_r$ in the direction that makes the observed pick more likely). 

> This may be seen as some form of [stochastic gradient descent](https://en.wikipedia.org/wiki/Stochastic_gradient_descent), where the randomness is in the data itself: which Cards were offered at each reward. 

By the derivatives above, for every option $o$ in $O_r$ the descent step is

$$R_o \leftarrow R_o + K \sum_{\text{games of } o \text{ in } r} \big(S_o - E_o\big)$$

where $K = \eta\log(10)/400.$ Explicitly, the pick $w_r$ wins each of its three games, so

$$R_{w_r} \leftarrow R_{w_r} + \sum_{\ell \neq w_r} \Delta_\ell, \qquad \text{and}\qquad R_\ell \leftarrow R_\ell - \Delta_\ell,$$

where $\Delta_\ell = K\,\big(1 - P(R_{w_r} > R_\ell)\big).$ This makes it so that an expected pick barely moves the ratings, while an upset (a lower-rated option picked) moves them by up to $K$ per game. Moreover, every update is zero-sum, so the ratings always average 1500.

> *The choice of $K$.* This parameter gives the largest change a single game can make. It thus sets the trade-off between following changes in preferences quickly (large $K$, faster forgetting) and staying steady against noise (small $K$, slower forgetting). We take $K = 16$ again from chess: it is the value Elo himself suggested for masters (with $K = 32$ for weaker players) and the one the USCF used for players above 2400. FIDE now uses values from 10 to 40, depending on the rating and experience of the player.

**What is not seen.**

- *Context.* As before.
- *Uncertainty.* A Card offered a few times stays near 1500 for lack of updates, not because it is average.
- *A fixed preference.* Ratings depend on the order of the rewards and weigh recent picks more.
- *The model's shape.* One number per option forces preferences to be consistent (preferring $a$ over $b$ and $b$ over $c$ implies preferring $a$ over $c$), which is not necessarily true in context. 

## WR vs. ELO

**Goal.** Test whether high-rated Cards (by the player) have higher WR, and flag the Cards with substantial mismatch.

**Data.**  All the same notation as in *Card Ratings*. We keep only the Cards $c$ with $n_c \ge 5$. With $m$ being the number of such cards, we demand that $m \ge 5$.

**Methods.**

(1) *[Spearman rank correlation](https://en.wikipedia.org/wiki/Spearman%27s_rank_correlation_coefficient).* We want to know whether $R_c$ and $a_c$ rise together. Since they are on unrelated scales (and their relation need not be a straight line), we compare only their orders: let $u_c$ and $u'_c$ be the ranks of $R_c$ and $a_c$, respectively, and consider their correlation

$$\hat\rho = \frac{\sum_c (u_c - \bar u)(u'_c - \bar u')}{\sqrt{\sum_c (u_c - \bar u)^2 \sum_c (u'_c - \bar u')^2}} \in [-1, 1].$$

We test $H_0: \rho \le 0$, against $H_1: \rho > 0$, where $\rho$ is the *true* rank correlation. The test statistic is

$$t = \hat\rho\ \sqrt{\frac{m - 2}{1 - \hat\rho^2}} \sim t_{m-2} \quad \text{(approximately) under } H_0.$$

Since $H_1$ is one-sided, the $p-$value is the probability, if $H_0$ were true, of a statistic at least as large as the one observed,

$$p = \mathbb P(T \ge t) = 1 - F_{m-2}(t), \qquad T \sim t_{m-2}.$$

(2) *[Exact binomial test](https://en.wikipedia.org/wiki/Binomial_test) per Card.* To flag single Cards, we test for each Card $c$ the hypothesis $H_0: k_c \sim \mathrm{Binomial}(n_c, e_c)$,  against $H_1$: it is not. The null hypothesis here should be read as saying that "Runs picking $c$ win as often as Runs that got as far as when $c$ was picked" (by the definition of $e_c$).

Since $n_c$ might be small and a Gaussian approximation can fail, we use the exact law: with $X \sim \mathrm{Binomial}(n_c, e_c)$, the $p-$value of Card $c$ is

$$p_c = \sum_{\substack{x = 0, \ldots, n_c \\ \mathbb P(X = x)\, \le\, \mathbb P(X = k_c)}} \mathbb P(X = x).$$

That is, $p_c$ is the probability, under $H_0$, of a number of wins at most as likely as the one observed.

(3) *Holm adjustment.* Testing $m$ Cards at once, some would be flagged by chance alone. So we adjust the $p-$values as in (4) of *HP lost per Fight type*. 

(4) *Flags.* Finally, we want to flag the Cards whose results go against the side of Skip they are rated on. We say that a Card $c$ is

- *Overpicked* if $R_c > R_{\mathrm{Skip}}$, but $a_c \le 0$.
- *Underpicked* if $R_c < R_{\mathrm{Skip}}$, but $a_c > 0$.

A flag is confirmed when the adjusted $p-$value is below 0.05, marked "possibly" when only $p_c$ is below $0.05$, and "leaning" otherwise. A Card whose results agree with its side of Skip is in line, whatever its $p-$value.

> **TODO.** Fit a line from ELO to WR and test each Card against its prediction. This would flag Cards rated far above or below Cards with similar results (i.e. Cards would not only be compared to Skip).

> **TODO.** Note each Run $j$ has its own WR $w(f_{jc})$, so $k_c$ is more accurately described as a sum of Bernoullis with different rates, i.e. a [Poisson binomial](https://en.wikipedia.org/wiki/Poisson_binomial_distribution). The variances of each model are such that $n_c e_c (1 - e_c) \ge \sum_j w(f_{jc})\big(1 - w(f_{jc})\big)$, so the current test errs towards fewer flags.

**What is not seen.** Besides the limits of $a_c$ (see *WR*):

- *Ratings relative to other Cards.* See the TODO above.
- *Each Run has its own expected rate*. See the TODO above.
- *Shared Runs.* A Run counts for every Card it picked, so the $a_c$ and $p-$values of different Cards are not independent, as Spearman's $p-$value assumes.
- *Different expected rates.* The test in (2) uses the average expected rate $e_c$ instead of that of each Run (see the TODO on the Poisson binomial above).
- *A strict adjustment.* Holm controls the chance of **at least** one false flag. [Benjamini–Hochberg](https://en.wikipedia.org/wiki/False_discovery_rate#Benjamini%E2%80%93Hochberg_procedure) keeps instead the expected **share** of false flags at 5%, which is (probably) better suited here.
