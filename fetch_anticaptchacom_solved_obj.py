from anticaptchaofficial.antigatetask import *


def solve_obj(passed_link, passed_email_login, passed_password):
    solver = antigateTask()
    solver.set_verbose(1)
    solver.set_key("bed08f5ead0c40e305175553e8f882e0")
    solver.set_website_url(passed_link)
    solver.set_template_name("SA automation")
    solver.set_variables({
        "email_login": passed_email_login,
        "password": passed_password
    })

    result = solver.solve_and_return_solution()
    if result != 0:
        # First fix sameSite values in cookiesRaw
        for cookie in result["cookiesRaw"]:
            # Convert "unspecified" to "None" which is what Playwright expects
            if cookie.get("sameSite") == "unspecified":
                cookie["sameSite"] = "None"
            # Ensure sameSite is capitalized properly
            elif cookie.get("sameSite") == "lax":
                cookie["sameSite"] = "Lax"

        # Now use the fixed cookiesRaw
        result["cookies"] = result["cookiesRaw"]
        result["origins"] = [{
            "origin": result["url"],
            "localStorage": [
                {"name": k, "value": str(v)}
                for k, v in result["localStorage"].items()
            ]
        }]

        with open('playwright/.auth/last_seekingalpha_state.json', "w") as f:
            json.dump(result, f, indent=4)
        with open('playwright/.auth/state_log.txt', 'a') as f:
            f.write(f"Last updated state: {datetime.today().strftime('%Y-%m-%d')} at {datetime.now()}")
        # print('Updated the json with the last profile')
        # print("cookies: ", cookies)
        # print("localStorage: ", localStorage)
        # print("fingerprint: ", fingerprint)
        # print("url: "+url)
        # print("domain: "+domain)
    else:
        print("task finished with error "+solver.error_code)


if __name__ == '__main__':
    solve_obj('https://seekingalpha.com/article/4726328-armour-residential-preferred-c-on-the-path-to-par', 'wise.investor.7783@gmail.com', '7878wiin')