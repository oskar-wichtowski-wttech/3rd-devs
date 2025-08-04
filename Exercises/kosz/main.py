import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_bracket_7_teams():
    fig, ax = plt.subplots(figsize=(20, 12))
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 30)
    ax.axis('off')

    def match_box(x, y, label, color='lightblue'):
        box = patches.FancyBboxPatch((x, y), 3.5, 1.5,
                                     boxstyle="round,pad=0.1",
                                     edgecolor='black', facecolor=color)
        ax.add_patch(box)
        ax.text(x + 1.75, y + 0.75, label, ha='center', va='center', fontsize=9, weight='bold')

    # Upper Bracket
    match_box(1, 20, "Seed 1 Golden Ticket", color='pink')
    
    match_box(1, 16, "Match A\nSeed 2 vs Seed 7")
    match_box(1, 12, "Match B\nSeed 3 vs Seed 6")
    match_box(1, 8, "Match C\nSeed 4 vs Seed 5")

    match_box(5.5, 14, "Match D\n\nWINNER A vs WINNER B")
    match_box(5.5, 10, "Match E\n\nWINNER C vs Seed 1")

    match_box(10, 16, "Match F\n\nWINNER D vs WINNER E")

    # Lower Bracket
    match_box(5.5, 6, "Match G\n\nLOOSER A vs LOOSER B", color='mistyrose')
    match_box(5.5, 3, "Match H\n\nLOOSER C vs LOOSER D", color='mistyrose')

    match_box(10, 3, "Match I\n\nWINNER G vs WINNER H", color='mistyrose')
    match_box(14.5, 8, "Match J\n\nLOOSER E vs WINNER I", color='mistyrose')

    match_box(19, 11, "Match K\n\nLOOSER F vs WINNER J", color='salmon')

    # Grand Final
    match_box(19, 16, "Grand Final\n\nWINNER F vs WINNER K", color='gold')

    # Labels
    ax.text(1, 18, "UPPER BRACKET", fontsize=12, weight='bold')
    ax.text(5.5, 7.75, "LOWER BRACKET", fontsize=12, weight='bold')
    ax.text(10, 22.2, "LOWER FINAL", fontsize=12, weight='bold')
    ax.text(19, 18.5, "GRAND FINAL", fontsize=12, weight='bold')

    plt.show()

draw_bracket_7_teams()
