import tkinter as tk
from tkinter import ttk
import threading

from core.catalog import get_catalog, sync_catalog
from core.queue import add_to_queue, cancel_all
from core.inspector import inspect_model
from core.favorites import toggle_favorite
from core.recommender import recommend
from core.tray import run_tray
from core.display import format_model
from core.agent_registry import list_agents
from core.bridge_controller import get_status, enable_bridge, disable_bridge


def launch_ui():

    catalog_cache = []
    selected_model = None


    app = tk.Tk()
    app.title("AI Model Hub - Command Center")
    app.geometry("1600x950")


    main = tk.Frame(app)
    main.pack(fill="both", expand=True)


    left = tk.Frame(main, width=300)
    left.pack(side="left", fill="y")


    center = tk.Frame(main)
    center.pack(side="left", fill="both", expand=True)


    right = tk.Frame(main, width=500)
    right.pack(side="right", fill="both")



    search_label = tk.Label(
        left,
        text="Search Models:"
    )

    search_label.pack(
        padx=10,
        pady=(10,0)
    )


    search_var = tk.StringVar()


    search = tk.Entry(
        left,
        textvariable=search_var
    )

    search.pack(
        padx=10,
        pady=5,
        fill="x"
    )


    listbox = tk.Listbox(left)

    listbox.pack(
        padx=10,
        pady=10,
        fill="both",
        expand=True
    )


    status = tk.Label(
        center,
        text="Ready"
    )

    status.pack()


    inspector = tk.Text(
        center,
        height=25
    )

    inspector.pack(
        fill="both",
        expand=True
    )


    task_label = tk.Label(
        center,
        text="Supervisor Task Console:"
    )

    task_label.pack()


    task_box = tk.Text(
        center,
        height=5
    )

    task_box.pack(
        fill="x"
    )


    output = tk.Text(
        center,
        height=10
    )

    output.pack(
        fill="both"
    )



    def execute_task():

        task = task_box.get(
            "1.0",
            tk.END
        )


        output.insert(
            tk.END,
            "\nRunning:\n" + task
        )


        def worker():

            from core.supervisor import run_task

            app.after(
                0,
                lambda: output.insert(
                    tk.END,
                    "\n[STATUS] Supervisor starting...\n"
                )
            )

            def status_update(message):

                app.after(
                    0,
                    lambda: output.insert(
                        tk.END,
                        f"\n[STATUS] {message}\n"
                    )
                )


            result = run_task(
                task,
                status_callback=status_update
            )

            app.after(
                0,
                lambda: output.insert(
                    tk.END,
                    "\n\nRESULT:\n" + result
                )
            )


        threading.Thread(
            target=worker,
            daemon=True
        ).start()



    tk.Button(
        center,
        text="Run Supervisor Task",
        command=execute_task
    ).pack()



    agents = tk.Text(
        right
    )

    agents.pack(
        fill="both",
        expand=True
    )







    bridge_frame = tk.LabelFrame(
        right,
        text="Bridge Control"
    )

    bridge_frame.pack(
        fill="x",
        padx=10,
        pady=10
    )


    bridge_enabled = False


    switch_canvas = tk.Canvas(
        bridge_frame,
        width=90,
        height=150,
        highlightthickness=0
    )

    switch_canvas.pack(
        pady=10
    )


    bridge_status = tk.Label(
        bridge_frame,
        text="Bridge: OFF"
    )

    bridge_status.pack()




    def draw_toggle():

        switch_canvas.delete(
            "all"
        )


        # vertical rectangular switch body

        if bridge_enabled:

            switch_canvas.create_rectangle(
                25,
                5,
                65,
                115,
                fill="green",
                outline="green"
            )

            # slider at top = ON

            switch_canvas.create_rectangle(
                30,
                15,
                60,
                45,
                fill="white",
                outline="white"
            )


        else:

            switch_canvas.create_rectangle(
                25,
                5,
                65,
                115,
                fill="red",
                outline="red"
            )

            # slider at bottom = OFF

            switch_canvas.create_rectangle(
                30,
                75,
                60,
                105,
                fill="white",
                outline="white"
            )


        switch_canvas.create_text(
            45,
            125,
            text="ON" if bridge_enabled else "OFF"
        )


    def refresh_bridge_status():

        nonlocal bridge_enabled

        state = get_status()

        bridge_enabled = bool(
            state.get("enabled")
        )


        bridge_status.config(
            text=
            "Online: "
            + str(state.get("online"))
            + " | Enabled: "
            + str(state.get("enabled"))
        )


        draw_toggle()



    def bridge_toggle_worker(target_state):

        if target_state:

            enable_bridge()

        else:

            disable_bridge()


        app.after(
            500,
            refresh_bridge_status
        )



    def toggle_bridge():

        nonlocal bridge_enabled

        target = not bridge_enabled

        bridge_enabled = target

        draw_toggle()


        threading.Thread(
            target=bridge_toggle_worker,
            args=(target,),
            daemon=True
        ).start()



    switch_canvas.bind(
        "<Button-1>",
        lambda event: toggle_bridge()
    )


    refresh_bridge_status()


    def refresh_agents():

        agents.delete(
            "1.0",
            tk.END
        )


        for agent in list_agents():

            agents.insert(
                tk.END,
                f"""
{agent['name']}
Type: {agent['type']}
Status: {agent['status']}
Description: {agent['description']}

"""
            )



    def refresh():

        nonlocal catalog_cache

        sync_catalog()

        catalog_cache = recommend(
            get_catalog()
        )

        listbox.delete(
            0,
            tk.END
        )


        for model in catalog_cache:

            listbox.insert(
                tk.END,
                model.get(
                    "name",
                    "unknown"
                )
            )


        refresh_agents()



    def on_select(event):

        nonlocal selected_model


        index = listbox.curselection()

        if not index:
            return


        name = listbox.get(
            index[0]
        )


        for model in catalog_cache:

            if model["name"] == name:

                selected_model = model
                break


        if selected_model:

            inspector.delete(
                "1.0",
                tk.END
            )

            inspector.insert(
                tk.END,
                format_model(
                    {
                        **selected_model,
                        **inspect_model(selected_model)
                    }
                )
            )



    listbox.bind(
        "<<ListboxSelect>>",
        on_select
    )



    search_var.trace_add(
        "write",
        lambda *_: refresh()
    )


    tk.Button(
        center,
        text="Refresh",
        command=refresh
    ).pack()


    tk.Button(
        center,
        text="Tray Mode",
        command=lambda:
        threading.Thread(
            target=run_tray,
            daemon=True
        ).start()
    ).pack()



    refresh()

    app.mainloop()






