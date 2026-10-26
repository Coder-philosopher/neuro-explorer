# Project Idea: Model Steering Studio (working title)

> This file is the starting brief for the AI agents who will build this project.
> Read it fully before doing anything. It describes **what I want**, not **how to do it**.
> How to do it is your job: research it, decide it, and build it.

---

## 1. What we are trying to build

Open-source AI models such as **Qwen** and **DeepSeek** have an enormous number of tiny internal parts (people call them neurons, and there are lakhs of them). Researchers have found that you can gently push some of these inner parts up or down, and the model's personality and style change: more poetic, more scientific, more formal, more like a particular character or avatar.

I want to build a **simple platform that lets anyone do this**, and **keeps a written record of everything we learn**.

In plain words, the platform should let me:

1. **Open a small open-source model** on my own computer.
2. **Find which inner parts control which behaviour** (poetic, scientific, friendly, formal, an avatar-like character, and so on).
3. **Turn those behaviours up or down with a simple dial**, then chat with the model and see the difference right away.
4. **Save the result** as a tweaked version of the model (or a small add-on file) that I can load again and run later.
5. **Write down everything** in a growing notebook of findings: for each inner part, where it lives, what it seems to do, how strong a push works well, and what goes wrong if pushed too hard. I call this the **Atlas**.

The Atlas matters as much as the dials. Every experiment we run should leave behind a clear note, so the next experiment starts smarter than the last one.

---

## 2. The big picture, in one paragraph

Imagine a mixing desk for an AI's personality. Each slider is a behaviour: poetic, scientific, calm, playful. I slide one up, chat with the model, and hear the change. When I find a good setting, I save it. Every slider I discover gets a page in the Atlas explaining what it does. Over time the Atlas becomes a map of the model's inner world, and we can combine sliders to shape a new version of the model on demand.

---

## 3. Honest expectations (please read)

- **We are not training a brand-new model from scratch.** That needs huge computers. We are **reshaping an existing open-source model**, so the result is a tweaked copy or a small add-on, built on top of the original.
- **One inner part usually does many unrelated things.** So a single "neuron" is often not a clean switch. You will probably need to group related parts into a **dial**. Figure out the best way to do this, and tell me in simple language what you chose and why.
- **Pushing too hard breaks the model** (it starts producing nonsense). The platform should show this clearly and help find the sweet spot.
- **Sometimes a plain instruction ("answer like a poet") works as well as or better than steering.** The platform should make it easy to compare both, so we learn when steering is actually worth it.
- **Do not pretend something works if it does not.** If an experiment fails, record the failure in the Atlas as well. Failures are useful.

---

## 4. My computer is small. This is a hard rule.

I do **not** have a powerful PC. Everything must be designed to work on:

- **Around 10 GB of memory**, or
- A **dual-core computer with about 6 GB of memory**.
- Assume **no strong graphics card** unless I say otherwise.

What this means for you:

- **Start with the smallest versions** of Qwen and DeepSeek. Big versions are out of reach on my machine.
- Use **shrunk / compressed model files** where possible so they fit in memory.
- Everything must work **one small step at a time**. No design that needs lots of memory at once.
- If a job is **too heavy for my PC** (for example, building the map of a model's inner parts), do not give up. **Find a free online way to do the heavy part** (free notebook services, free community resources), then bring the finished result back to my machine. Tell me clearly when this happens and walk me through it.
- **Always tell me the memory and time cost** of a step before I run it, in plain words ("this will take about 20 minutes and use about 4 GB").
- Never freeze my computer. If something is too big, stop and report instead of trying anyway.

---

## 5. The platform itself

I want a **web-based platform that runs locally on my own computer** (open it in the browser, nothing sent to anyone else's servers).

It should have, at minimum:

- **A chat window** to talk to the model, with the dials beside it.
- **A model picker** to download or load a small open-source model.
- **A dial panel** to find, turn up, turn down, and combine behaviours.
- **Side-by-side comparison**: normal model vs. steered model, same question.
- **The Atlas viewer**: browse, search and read all the notes. Each entry should show where the part lives, what it controls, which settings worked, and examples of before and after.
- **A built-in workspace where I can write and run code modules**, so I can add new features to the platform from inside the platform itself. Think of it as a small code editor plus a place to run scripts and see results, all in the same browser page.
- **A project log** that records every experiment automatically (what we tried, what happened, how long it took).
- **Save and load** for steered models and dial settings.

Keep the design **clean and simple**. I should not need to be an expert to use it.

---

## 6. How I want you to work (this is the important part)

**You have a free hand.** I am deliberately not telling you which tools or methods to use. Decide for yourselves.

### Research first
- **Search the internet** for how researchers and companies already do this kind of model steering and inner-part mapping.
- Look for **existing open-source projects and tools**, and **pull from GitHub** whenever a good one already exists. **Do not rebuild what already exists.**
- Prefer **free, open-source** libraries and platforms with licences that allow this use. Check the licence of everything you borrow and note it.
- Use **current** information. Tools and models change fast, so verify versions and availability before depending on them.
- Write a short **research summary in plain language** before you start building: what exists, what you plan to reuse, what you plan to build, and what is risky.

### Work as a crew
Set up a **crew of AI helpers** (use whatever open-source agent tools fit best), with clear roles. For example:

- **Researcher**: finds projects, papers, tools, and examples.
- **Builder**: writes the code and assembles the platform.
- **Tester**: tries to break things and checks that it runs on small hardware.
- **Documenter**: keeps the Atlas, the project log, and the plain-language guides up to date.
- **Reviewer**: checks the work, flags risks, and keeps the project honest.

You may rename, add or merge roles. Decide the best crew for each stage.

### Build in stages
Do not try to build everything at once. Work in stages, and **at the end of each stage, stop, show me a working result, and explain it simply** before moving on. Suggested stages (change them if you find better ones):

1. **Research and plan**: what exists, what we reuse, what we build.
2. **Get one tiny model running** on my machine and chat with it.
3. **First dial**: make a single behaviour (for example "poetic") work and show the before and after.
4. **Local web platform, first version**: chat, one or two dials, comparison view.
5. **The Atlas**: automatic notes for every experiment, plus a viewer.
6. **Many dials**: discover more behaviours (scientific, formal, playful, avatar-like), combine them, find safe strength limits.
7. **Save, load, and share** steered models and settings.
8. **Built-in code workspace** for adding new modules.
9. **Polish, speed, and clear guides** for anyone who wants to try it.

### Keep me informed
- Explain things **in plain language**. If you must use a technical word, explain it in one line.
- Tell me **what you decided and why**, especially when you chose between options.
- Tell me **what you are unsure about**. Do not hide uncertainty.
- Ask me a question **only when you are truly stuck**; otherwise make a sensible choice and note it.

---

## 7. What "done" looks like

The first milestone is reached when I can:

1. Start the platform on my own low-spec computer with simple instructions.
2. Load a small Qwen or DeepSeek model.
3. Turn at least **three different behaviours** up and down (for example poetic, scientific, formal) and see a clear, repeatable change in the answers.
4. See a **side-by-side** of the normal and steered model.
5. Save a steered setting, reload it later, and get the same behaviour.
6. Open the **Atlas** and read a clear note for every dial and experiment we ran, including the failures.

After that, we grow: more models, more dials, better Atlas, and better tools.

---

## 8. Starting leads (hints, not instructions)

These are names I came across while exploring the idea. They are **leads to check**, not requirements. Verify them, and replace them with better options if you find any.

- **Neuronpedia**: an open platform for browsing, labelling and steering inner parts of models. A good example of what the Atlas could look like.
- **Goodfire**: a company offering hosted model-steering tools. Useful to study, but not open-source.
- **SAELens, TransformerLens, nnsight**: open-source tools for reading and editing a model's inner activity.
- **EleutherAI auto-interp**: open-source tool that uses an AI to automatically write labels for inner parts.
- **repeng** and **llama.cpp control vectors**: lightweight ways to steer a model without heavy training, probably the best fit for my small computer.
- **Gemma Scope** (Google DeepMind): a large public set of already-mapped inner parts, useful for learning how the finished product looks.
- An **AWS sample project** that shows feature search, steering, and mapping a small Qwen model, which could be a good template.

Also search for anything newer. This area moves quickly.

---

## 9. Rules to follow throughout

- **Open source and free first.** Ask before using anything paid.
- **Everything runs locally** after the initial downloads.
- **Keep the project folder tidy**: code, notes, Atlas entries, saved models and logs each in clear places.
- **Save progress often** and make it easy to resume if my computer restarts.
- **Credit and licence**: keep a list of every project and model used, with its licence.
- **Safety**: the platform is for understanding and shaping model style and behaviour. Do not build features meant to cause harm, and tell me if a request seems to head that way.