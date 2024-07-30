# Constants for the servo names and leg names
LEGS = ["Leg 1", "Leg 2", "Leg 3", "Leg 4"]
SERVOS = ["Hip", "Knee", "Ankle"]

# Initial angles for each servo
initial_angles = {
    "Leg 1": {"Hip": 90, "Knee": 90, "Ankle": 90},
    "Leg 2": {"Hip": 90, "Knee": 90, "Ankle": 90},
    "Leg 3": {"Hip": 90, "Knee": 90, "Ankle": 90},
    "Leg 4": {"Hip": 90, "Knee": 90, "Ankle": 90},
}

# Function to update servo angles (stub for actual hardware interaction)
def set_servo_angle(leg, servo, angle):
    # Here you would have code to set the servo angle in the actual hardware
    pass

# Main function for the CLI interface
def adjust_servo_angles():
    current_leg = 0
    current_servo = 0

    while True:
        # Display the current selection and angles
        print("\n" * 50)  # Clear the screen by printing new lines
        for i, leg in enumerate(LEGS):
            if i == current_leg:
                print(f"> {leg}:")
            else:
                print(f"  {leg}:")
            for j, servo in enumerate(SERVOS):
                angle = initial_angles[leg][servo]
                if i == current_leg and j == current_servo:
                    print(f"    > {servo}: {angle}°")
                else:
                    print(f"      {servo}: {angle}°")

        # Prompt for user input
        print("\nUse arrow keys (u/d/l/r) to navigate, 'w' to increase, 's' to decrease, 'q' to quit.")
        key = input("Enter command: ").lower()

        if key == 'u':  # Up (previous servo)
            current_servo = (current_servo - 1) % len(SERVOS)
        elif key == 'd':  # Down (next servo)
            current_servo = (current_servo + 1) % len(SERVOS)
        elif key == 'l':  # Left (previous leg)
            current_leg = (current_leg - 1) % len(LEGS)
        elif key == 'r':  # Right (next leg)
            current_leg = (current_leg + 1) % len(LEGS)
        elif key == 'w':
            # Increase the angle of the current servo
            initial_angles[LEGS[current_leg]][SERVOS[current_servo]] += 1
            # Clamp the angle between 0 and 180
            initial_angles[LEGS[current_leg]][SERVOS[current_servo]] = min(180, initial_angles[LEGS[current_leg]][SERVOS[current_servo]])
            set_servo_angle(LEGS[current_leg], SERVOS[current_servo], initial_angles[LEGS[current_leg]][SERVOS[current_servo]])
        elif key == 's':
            # Decrease the angle of the current servo
            initial_angles[LEGS[current_leg]][SERVOS[current_servo]] -= 1
            # Clamp the angle between 0 and 180
            initial_angles[LEGS[current_leg]][SERVOS[current_servo]] = max(0, initial_angles[LEGS[current_leg]][SERVOS[current_servo]])
            set_servo_angle(LEGS[current_leg], SERVOS[current_servo], initial_angles[LEGS[current_leg]][SERVOS[current_servo]])
        elif key == 'q':
            break

# Run the main function
if __name__ == "__main__":
    adjust_servo_angles()
