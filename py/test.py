import utils

sps = utils.get_system_prompts()

for i, uid in enumerate(sps["uid"]):

    sp = utils.build_system_prompt(uid)

    print(f"{i+1}: {sp}\n")
