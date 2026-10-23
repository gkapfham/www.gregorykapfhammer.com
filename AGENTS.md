## Writing Agent Instructions

## Introduction

As a writing agent, you must adhere to the following instructions when making
changes to this repository. Your primary goals are as follows:

- Write blog posts that summarize already published research papers
- Write blog posts that summarize recent episodes of the Software
  Engineering Radio podcast

This repository contains the professional website for Gregory M. Kapfhammer.
These content that you write for this website must meet certain requirements so
as to ensure that it correctly aligns with prior content and offers
professional, technical content suitable for a professor's website.

## Blog Posts About Software Engineering Radio Episodes

These are the high-level requirements for the blog posts about episodes of the
Software Engineering Radio podcast:

- The prompt you receive will specify:
  - A text file that will contain the transcript of the episode
  - A template file in which you can place your content
  - The link to the blog post on the Software Engineering Radio website
  - The link to the MP3 file of the Software Engineering Radio episode
- You must first take these steps:
  - Read the entire transcript that is provided in the text file
  - Review all the prior blog posts about episodes of the Software
    Engineering Radio podcast for which I was a co-host. You will know which of
    the prior blog posts in the `blog/` directory are about episodes of the
    Software Engineering Radio podcast because you will see, for instance, the
    following inside of the metadata at the top of the file: `categories: [post, software development, software engineering radio]`. Note in
    particular that you are looking for the `software engineering radio`
    category inside of the metadata.
- The purpose of the blog post is to highlight the key questions that were
  asked and answered in the episode and to then encourage the reader of the blog
  post to listen to the full episode of the podcast. These posts should be short
  and not attempt to summarize all the questions or take-home points in the
  episode.
- Each blog post must follow this structure:
  - **Introduction** section links to the website for the episode and the
    website of the person who I interviewed. This section should also
    appropriately express the importance of my interview and my thanks for the
    guest coming on the show.
  - In the **Introduction** section, there should be a brief, high-level
    overview of some of the key insights that emerged from the episode.
  - In the **Insights** section, you must provide at least three but no more
    than five questions that I asked during the interview. Since the transcript
    may not perfectly record exactly how I asked the question, you may need to
    slightly infer the exact question that I asked. Then, you need to use
    direct quotes from the transcript of the interview that are the response
    given by the guest to the question.
  - In the **Listen** section, you must provide a link to the various
    platforms on which it is possible to listen to Software Engineering Radio.
    You can look at the other blog posts that I have already written to get
    these links, which include, for instance, Apple Podcasts and Spotify.
    Please note that this content does not need to link to the specific episode
    but rather link to the general Software Engineering Radio page on the
    specified platform. Finally, you need to embed the episode player with
    the `podcast` shortcode that I have set up with Quarto. It takes the MP3
    file, the episode number, and the episode title, and it renders the
    player with the correct kicker line. Here is a complete example of what
    that would look like:

```markdown
{{< podcast
src="https://traffic.libsyn.com/secure/forcedn/seradio/666-eran-yahav-tabnine-coding-assistant.mp3"
episode="666"
title="Eran Yahav on the Tabnine AI Coding Assistant" >}}
```

    The shortcode accepts these arguments:

    - `src` (required): the URL of the MP3 file
    - `title` (required): the episode title, without the `SE Radio <number>:`
      prefix, because the kicker already shows the episode number
    - `episode` (optional): the episode number, used to build the kicker
    - `show` (optional): defaults to Software Engineering Radio
    - `label` (optional): replaces the whole kicker line
    - `download` (optional): defaults to `src`

- You will know what link to provide since I will give that to you in the
prompt for writing this blog post.
- Make sure to include `{{< include /_back-blog.qmd >}}` at the end of the
file as this code is needed to ensure that the "back link" works.
- After you write the post, you must verify it with the tool that lives in
  `_tools/verify-seradio-post.py`; `README.md` documents the tool and every
  option that it supports. The tool checks that every quotation appears
  verbatim in the transcript, that the front matter and the required sections
  are present, and that the prose fits in 80 columns. Run the command below
  with the slug of the new post and the number of the episode:

  ```bash
  uv run _tools/verify-seradio-post.py \
      --post blog/<slug>/index.qmd --episode <number> --check-links
  ```

- The tool prints a table that pairs each quotation with the speaker and the
  timestamp of the transcript turn that contains it. That table is the
  evidence that the "Support your work" rule requires. A non-zero exit code
  means that at least one check failed, so fix the post and run the tool
  again.
- Use the tool in `_tools/fetch-seradio-transcript.py` to download the
  transcript of an episode when the prompt does not provide one, and to learn
  the details of an episode before you write the post. The tool reports the
  episode number, the title, the number of speaker turns, and the URL of the
  MP3 file together with the Quarto podcast shortcode that the **Listen**
  section needs. It caches the transcript outside of the repository, and the
  `--stdout` option prints the transcript on its own so that you can search
  it while writing:

  ```bash
  uv run _tools/fetch-seradio-transcript.py --url <episode-page-url>
  ```

## Blog Posts About Research Papers

These are the high-level requirements for the blog posts about research papers:

- The prompt you receive will specify:
  - A PDF file of the actual research paper
  - A template file in which you can place your content
  - The key that you will use to reference the paper in the blog post
- You must first take these steps:
  - Read the entire research paper by converting it from PDF to text (or,
    take any additional steps that you need to take to read the entire paper)
  - Identify the "pain point" that the paper surfaces and solves and why it
    is important for the research paper solve this problem
  - Identify the key contributions of the specified research paper
  - Identify the key technical terms and concepts used in the research paper
  - Identify any figures or tables that are essential to understanding the
    research paper
  - Review all the prior blog posts about research papers. You will know
    which of the prior blog posts in the `blog/` directory are about research
    papers because you will see, for instance, the following inside of the
    metadata at the top of the file: `categories: [post, research paper, database testing]`. Note in particular that you are looking for the
    `research paper` category inside of the metadata.
- The purpose of the blog post is to highlight the key details of the research
  paper and to then encourage the reader of the blog post to read the full paper.
- Each blog post must follow this structure:
  - **Introduction** section to the blog post for the research paper that
    asks a question. You will notice that each of the research papers should
    identify a "pain point" that is something that does not work or is not well
    understood or is under studied. Make sure that you highlight this "pain
    point" in the introduction.
  - In the **Introduction** section, a reference to the actual research paper
    using the required format that Quarto and the layout of this blog requires.
    Here is an example of what a paper reference would look like: `[@Clark2011] [{{< iconify fa6-solid book-open>}}](/research/papers/clark2011/index.qmd)`. You will know what
    specific key is needed, like `Clark2011` because I will provide that to you
    in the prompt for writing the blog post.
  - **Key Contributions** section that lists the key contributions of the
    research paper in a bulleted list. Make sure that each one of the specific
    contributions is given a name like `Automated Technique`.
  - **Empirical Results** section that lists the empirical results of the
    paper. Please only include numbers in the overview of the results if you
    can ensure that you get the numbers exactly right. If the number does not
    appear in the provided paper, then you cannot include it in the blog post.
  - In the **Future Work** section, you must provide a brief summary of the
    future work that the authors of the paper suggest. This is often a short
    paragraph that will be in the conclusion of the paper, normally at the end.
  - In the **Further Details** section, you must provide a brief summary of
    my work in this area and how I plan to continue to explore this topic. This
    should also invite the reader of the blog post to contact me and/or
    subscribe to my mailing list. This content must be in a Quarto callout that
    is created in the following fashion: `::: {.callout-note appearance="simple"}`.
  - Make sure to include `{{< include /_back-blog.qmd >}}` at the end of the
    file as this code is needed to ensure that the back link works.

## Additional Rules for All Blog Posts

These are aspects of any blog post that you must avoid:

- Do not include any personal opinions or subjective statements not in the paper.
- Do not write a sentence in the blog post that is exactly the same as in the paper.
- Do not give the blog post a title that is exactly the same as the paper.
- Do not write content with too much technical jargon or with an assumption
  about the audience's knowledge of the specific research topic.
- Do not write in a fashion that is too "over the top" since that would not
  fit for the professional website of a professor. The tone should be
  professional, technical, and academic unless there is a clear goal that
  you can achieve with a different type of writing style.
- Do not create links to pages on the Web that do not exist.

These are the high-level rules about modifying the files in this repository:

- **Line width:** All text files, including Markdown and source code, should
  have a line width of 80 characters.
- **Permission to run commands:** You have permission to run all commands that
  are built-in to the command-line agent to work on the episode outlines.
- **Incremental changes:** Make small, incremental changes. This makes it
  easier to review your work and catch errors early.
- **Communicate clearly:** When you propose changes, explain what you've done
  and why and make it clear what rules you followed and why you followed them.
- **Use examples:** This repository contains examples of multiple blog posts
  that Gregory M. Kapfhammer already wrote about research papers and episodes of
  the Software Engineering Radio podcast. You should study these prior examples
  so as to make sure that you write with the correct tone.
- **Support your work:** Once you are finished writing the blog post, you need
  to make sure that you provide quotations to support the sentences that you
  wrote. For a blog post about a research paper, you should, for instance,
  provide quotations that support your summary of the key empirical results. For
  a blog post about an episode of the Software Engineering Radio podcast, you
  should provide the exact extracts from the transcript that you used to create
  the answers from the guest that are in the blog post. You don't need to write
  this into the file; instead you should produce this as output in the terminal.
  For a Software Engineering Radio post, the `_tools/verify-seradio-post.py`
  tool prints this evidence for you.
- **Check your links**: If you add a link to a web site in any file for this
  web site, you must check that the link exists on the internet and it is valid.
  For a Software Engineering Radio post, the `--check-links` option of
  `_tools/verify-seradio-post.py` automates this check.

As a writing agent, you must also follow these behavior guidelines, especially
when it comes to notifying the podcast host about your work and status:

- The user has given permission to use the `notify-send` command to signal task
  completion. Here is an example of the command: `notify-send "Question from the Writing Agent" "Please clarify how to complete the writing task."`.
- The user wants a `notify-send` notification whenever I ask a question.
- Always notify the user with `notify-send` when a task is complete or when
  feedback is needed. I have standing permission to use the notification tool.

### Terminal-Browser Workflow

`terminal-browser` provides a live browser connection that is especially useful
for inspecting the rendered Quarto site. It supplies both an accessibility tree
and screenshots, so it complements source inspection and DOM measurements.

#### Browser ownership and startup

- First run `terminal-browser ls --all`, not only `terminal-browser ls`.
- The plain command can hide browsers opened in another terminal. The `--all`
  form reports their browser keys, tabs, URLs, and CDP targets.
- If this agent is running inside Zellij and no browser is listed, do not assume
  that `terminal-browser open` will work. It can fail because Zellij is not a
  recognized Ghostty pane.
- In that situation, ask the user to run the following in a standalone Ghostty
  terminal:

  ```bash
  terminal-browser open http://localhost:5559/slides/weektwo/
  ```

- Starting the browser first is helpful and, from a Zellij session, is normally
  necessary for the agent to access it. Once it is running, the agent can use
  `terminal-browser ls --all` and connect to it by browser key.
- If the agent itself is running from a recognized Ghostty pane, it may start
  the browser with `terminal-browser open <url>` or open a tab with
  `terminal-browser new-tab <url> --browser <key>`.
- Record whether the browser existed before the verification. Never shut down a
  browser that the user started. The agent may close only a browser or tab that
  it started, and only when doing so will not affect another task.

#### Connecting and inspecting a page

After finding a browser key, use the browser-specific action interface:

```bash
terminal-browser action --browser <key> -- snapshot
terminal-browser action --browser <key> -- screenshot /tmp/weektwo.png
terminal-browser action --browser <key> -- eval 'document.title'
```

- `snapshot` returns the live accessibility tree, including headings, bullets,
  code, output, links, and interactive references such as `@e14`.
- Use those references with commands such as
  `terminal-browser action --browser <key> -- click @e14`.
- Use `screenshot` to inspect the actual rendered pixels. The screenshot may
  use a high device-pixel-ratio, so also query `innerWidth` and `innerHeight`.
- Use `eval` for computed browser information, not guesses based only on the
  source file. For example:

  ```javascript
  JSON.stringify({
    url: location.href,
    viewport: [innerWidth, innerHeight],
    slide: document.querySelector("section.present")?.id
  })
  ```

- If the target browser has no pane, use its browser key or CDP target from
  `terminal-browser ls --all`; `no pane` does not mean that it is inaccessible.
- Use `terminal-browser new-tab <url> --browser <key>` when a separate target
  URL is needed. Do not change the user's active tab unnecessarily.

#### Measuring page quality

Use a browser evaluation to identify wasted wrapping and overflow:

```javascript
const slide = document.querySelector("section.present");
const measurements = [...slide.querySelectorAll("li, p, h1, h2")].map((el) => {
  const range = document.createRange();
  range.selectNodeContents(el);
  const rects = [...range.getClientRects()];
  return {
    text: el.innerText,
    lines: rects.length,
    width: el.getBoundingClientRect().width,
    height: el.getBoundingClientRect().height
  };
});
JSON.stringify(measurements);
```

- A second line containing only one or two words is a content-editing problem,
  not a font-size problem.
- Rewrite the sentence into one useful line, or deliberately make both lines
  useful. Do not use `white-space: nowrap` to hide a poor sentence.
- Temporarily reveal fragments only in a disposable inspection copy when the
  hidden state would prevent measurement. Remove that copy afterward.
- Test code slides and takeaway boxes with all relevant output visible. Check
  both `scrollWidth > clientWidth` and `scrollHeight > clientHeight`.

#### Shutdown rules

- Do not run `terminal-browser shutdown` merely because verification is done;
  it may terminate the user's browser session.
- Leave a user-owned browser running and report that it remains available.
- If the agent created an isolated browser and the user explicitly permits
  cleanup, close its tab or stop its browser after deleting temporary
  screenshots and inspection artifacts.

## Additional Rules for Version Control

- Do not commit code.
- Do not push code to the GitHub repository.
- Do not merge pull requests.
