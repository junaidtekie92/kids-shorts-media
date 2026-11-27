# Kids Shorts – overnight run

Each run makes **one** new kids Short and schedules it on Junaid's YouTube kids channel through Metricool.
Videos are released at 3 fixed times a day; making them is faster than releasing them, so a queue builds up.

## Steps for one run

1. **Get the repo.** Attach `junaidtekie92/kids-shorts-media` with push access, then
   `git clone --depth 1 https://github.com/junaidtekie92/kids-shorts-media /home/claude/kids-shorts-media`.
2. **Pick the episode.** The first entry of `episodes.json` whose `id` is not in `ledger.json → done`.
   - If every episode is done, add 10 new ones to `episodes.json` in the same format first.
     Use only icons that exist in `tool/icons/` (Twemoji codes), keep every fact simple and true
     (a banana is yellow, a cow says "Moo"), vary the theme (`sky`, `night`, `beach`, `candy`),
     the type (`count` or `cards`) and the subject, and never repeat an existing title.
3. **Check the look.** `python3 tool/gen.py ID --stills`, open the two PNGs in `/tmp` and look at them.
   Text must not overlap or run off the screen. Fix the spec if it does.
4. **Render.** `python3 tool/gen.py ID` writes `videos/ID.mp4`.
5. **Push the video.** Commit `videos/ID.mp4` and push to `main`
   (`git -c push.negotiate=true push origin main`).
   Its public link is `https://raw.githubusercontent.com/junaidtekie92/kids-shorts-media/main/videos/ID.mp4`.
6. **Pick the release time.** Slots are `ledger.json → slots_taipei` (Asia/Taipei).
   Use the earliest slot that is later than both (a) the latest `publish_at` in `ledger.json → done`
   and (b) now + 30 minutes.
7. **Schedule it.** First call Metricool `getScheduledPosts` and make sure this video is not already
   scheduled (no duplicates). Then `createScheduledPost` with `blogId` `8397036`, the raw link as `media`,
   provider `youtube`, `text` = `yt.description`, and
   `youtubeData = {title: yt.title, type: "short", privacy: "public", tags: yt.tags, category: "EDUCATION",
   madeForKids: true, isAiGeneratedContent: false}`.
8. **Record it.** Append `{"id", "publish_at", "metricool_id"}` to `ledger.json → done`, commit, push.

## Rules

- Only our own original animations. Never download or re-use anyone else's video, music or characters.
- Always `madeForKids: true`.
- One video per run. If any step fails, stop and say what failed; do not post twice.
