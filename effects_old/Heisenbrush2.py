import sys
import os
import numpy as np
from PIL import Image, ImageDraw
import random
import pygame

# List of effect-specific requirements
REQUIREMENTS = ["Color", "Strength", "Orientation"]

class BaseEffect:
    """Base class for all effects"""
    def __init__(self):
        self.parameters = {}
        self.requirements = []
        self.label = "Base Effect"

    def add_property(self, property):
        self.parameters[property.label] = property.value

    def run_job(self, job_id):
        # Placeholder for compatibility
        pass

class Heisenbrush2(BaseEffect):
    def __init__(self, *args):
        super().__init__()
        self.label = "Quantum Heisenberg Effect"
        self.requirements = REQUIREMENTS
        self.properties = {}

        # Store the properties passed from the editor
        for arg in args:
            if hasattr(arg, 'label'):
                self.add_property(arg)

    def add_property(self, property):
        """Add a property to the effect parameters"""
        self.parameters[property.label] = property.value
        self.properties[property.label] = property

    def build(self):
        """Prepare data for the effect"""
        # Get parameters with defaults for safety
        self.color = self.parameters.get("Color", (255, 255, 255))
        self.strength = float(self.parameters.get("Strength", 0.5))
        self.points = self.parameters.get("Points", [])
        self.radius = int(self.parameters.get("Radius", 10))
        self.vertical = (self.parameters.get("Orientation", "vertical") == "vertical")

        # Will be created later in apply()
        self.new_image = None

    def numbers_to_rgb_colors(self, numbers):
        """
        Convert a list of numbers between 0 and 1 into RGB values.
        """
        rgb_colors = []

        for num in numbers:
            # Ensure number is between 0 and 1
            num = max(0, min(1, num))

            # Generate a color based on the value
            # Use HSV color space for more interesting variations
            hue = num * 360  # Map value to hue (0-360)
            saturation = 0.7 + 0.3 * ((num * 17) % 1.0)  # Varied saturation
            value = 0.5 + 0.5 * ((num * 23) % 1.0)  # Varied brightness

            # Convert HSV to RGB
            h = hue / 60
            i = int(h)
            f = h - i
            p = value * (1 - saturation)
            q = value * (1 - saturation * f)
            t = value * (1 - saturation * (1 - f))

            if i == 0:
                r, g, b = value, t, p
            elif i == 1:
                r, g, b = q, value, p
            elif i == 2:
                r, g, b = p, value, t
            elif i == 3:
                r, g, b = p, q, value
            elif i == 4:
                r, g, b = t, p, value
            else:
                r, g, b = value, p, q

            # Convert to 0-255 range
            rgb_colors.append((int(r * 255), int(g * 255), int(b * 255)))

        return rgb_colors

    def simulate_quantum_results(self, distances):
        """
        Simulates quantum computation results without actual quantum hardware.
        """
        # Initialize random seed based on distances
        seed_val = int(sum(distances) * 1000) if distances else 0
        random.seed(seed_val)

        # Generate some "quantum-looking" results based on the distances
        values = []
        phase = random.random() * 6.28  # Random initial phase

        for d in distances:
            # Generate values with quantum-like characteristics:
            # - Wave-like behavior (sine functions)
            # - Some randomness (quantum uncertainty)
            # - Influence from previous values (entanglement-like)

            if values:
                # Add some dependency on previous values (like entanglement)
                prev = values[-1]
                # Quantum interference pattern
                value = 0.5 + 0.5 * np.sin(d * 3 + phase) * np.cos(prev * 5)
                # Add quantum "noise"
                value = 0.7 * value + 0.3 * random.random()
            else:
                # First value
                value = 0.5 + 0.5 * np.sin(d * 3 + phase)
                value = 0.7 * value + 0.3 * random.random()

            values.append(value)

        # Normalize to 0-1 range
        min_val = min(values) if values else 0
        max_val = max(values) if values else 1
        if max_val > min_val:
            values = [(v - min_val) / (max_val - min_val) for v in values]

        return values

    def reset(self):
        """Reset the effect state"""
        self.points = []

    def interpolate_points(self, points, steps=10):
        """Interpolate between points for smoother brush strokes"""
        if len(points) < 2:
            return points

        interpolated = []
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]

            # Add the starting point
            interpolated.append((x1, y1))

            # Interpolate between current and next point
            for step in range(1, steps):
                t = step / steps
                x = int(x1 + t * (x2 - x1))
                y = int(y1 + t * (y2 - y1))
                interpolated.append((x, y))

        # Add the last point
        interpolated.append(points[-1])

        return interpolated

    def apply(self):
        """Apply the quantum brush effect to the image"""
        try:
            # Make sure we have enough points to work with
            if not hasattr(self, 'points') or not self.points or len(self.points) < 2:
                print("Not enough points for Heisenbrush2 effect")
                return None

            # Get the image from the canvas
            img_path = self.parameters.get("File", "")
            if img_path:
                original_image = Image.open(img_path)
            else:
                # Create a default white image
                original_image = Image.new("RGB", (512, 512), "white")

            # Make a copy to work with
            self.new_image = original_image.copy()
            draw = ImageDraw.Draw(self.new_image)

            # Calculate distances between consecutive points
            distances = []
            for i in range(len(self.points) - 1):
                x1, y1 = self.points[i]
                x2, y2 = self.points[i + 1]
                distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                distances.append(distance)

            # Apply strength parameter to the distances
            if distances:
                # Normalize distances and apply strength
                distances = np.array(distances)
                max_dist = np.max(distances) if np.max(distances) > 0 else 1
                distances = self.strength * distances / max_dist

                # Get simulated quantum results based on the distances
                quantum_values = self.simulate_quantum_results(distances)
                new_colors = self.numbers_to_rgb_colors(quantum_values)

                # Create interpolated points for smoother drawing
                inter_points = self.interpolate_points(self.points)

                # Map colors to interpolated points
                point_colors = []
                step_size = len(inter_points) / (len(new_colors) or 1)

                for i, point in enumerate(inter_points):
                    # Determine which color to use based on position
                    color_idx = min(int(i / step_size), len(new_colors) - 1)
                    if color_idx < 0:
                        color_idx = 0
                    point_colors.append((point, new_colors[color_idx]))

                # Draw brush strokes with quantum colors
                for (x, y), color in point_colors:
                    # Convert point coordinates if needed
                    # The y,x order is because sometimes image coordinates are flipped
                    draw.ellipse(
                        [(y - self.radius, x - self.radius),
                         (y + self.radius, x + self.radius)],
                        fill=color
                    )

            return self.new_image
        except Exception as e:
            print(f"Error in Heisenbrush2.apply(): {e}")
            import traceback
            traceback.print_exc()
            return None

    def run_brush(self, canvas, effect_name=None):
        """Run the brush effect on the canvas - required for editor integration"""
        try:
            # Store the file path from the canvas
            self.parameters["File"] = canvas.file_path.value

            # Build and apply the effect
            self.build()
            result = self.apply()

            if result:
                # Update the canvas with the new image
                canvas.update_image(result)

            # Reset points for next application
            self.points = []

        except Exception as e:
            print(f"Error running brush: {e}")
            import traceback
            traceback.print_exc()

    def handle_event(self, event):
        """Handle mouse events for the brush"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Start collecting points when mouse is pressed
            self.points = [event.pos]
            return True

        elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
            # Add points as the mouse moves
            self.points.append(event.pos)
            return True

        return False

    def draw(self, screen, mouse_pos):
        """Draw the brush preview on screen"""
        # Draw a circle representing the brush cursor
        if hasattr(self, 'radius'):
            import pygame
            pygame.draw.circle(screen, (100, 100, 100), mouse_pos, self.radius, 1)

if __name__ == "__main__":
    # For standalone testing
    if len(sys.argv) < 2:
        print("Please provide an ID as a command-line argument.")
        sys.exit(1)

    brush = Heisenbrush2()
    brush.run_job(sys.argv[1])