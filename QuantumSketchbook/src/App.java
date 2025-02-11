import processing.core.PApplet;
import java.util.HashMap;
import java.util.Map;

public class App {
	PApplet parent; // Reference to the main sketch
	
	private boolean running;
	private HashMap<String, Property> buttons;
	private Sketchbook canvas;
	
	public App(PApplet pa) {
		parent = pa; // Set the connection between the Processing sketch and user instance
	}
	
	public void update() {
		// Put the logic for Processing's draw()
		parent.background(255);
		parent.fill(0);
		parent.textSize(32);
		parent.text("Hello world!", 100, 100);
	}
}
