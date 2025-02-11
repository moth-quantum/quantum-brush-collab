import java.awt.*;
import java.awt.event.*;

public class Property {
	String label;
	Object value;
	Object defaultValue;
	String type;
	Rectangle rect;
	Font font = new Font("Arial", Font.PLAIN, 24);
	
	public Property(String label, Object value, String type) {
		this.label = label;
		this.value = value;
		this.type = type;
		this.defaultValue = value;
	}
	
	public void setPosition(int x, int y) {
		this.rect = new Rectangle(x, y, 190, 30);
	}
	
	public void reset() {
		this.value = defaultValue;
	}
	
	public void draw(Graphics g) {
		g.setFont(font);
		if ("text".equals(type)) {
			g.setColor(Color.gray);
			g.fillRoundRect(rect.x, rect.y, rect.width, rect.height, 10, 10);
			g.setColor(Color.black);
			g.drawRoundRect(rect.x, rect.y, rect.width, rect.height, 10, 10);
			g.drawString(label + ": " + value.toString(), rect.x + 5, rect.y + 20);
		}
		else if ("toggle".equals(type)) {
			g.setColor((boolean) value ? Color.green : Color.red);
			g.fillRoundRect(rect.x, rect.y, rect.width, rect.height, 10, 10);
			g.setColor(Color.black);
			g.drawRoundRect(rect.x, rect.y, rect.width, rect.height, 10, 10);
			g.drawString(label, rect.x + 5, rect.y + 20);
		}
	}
	
	public boolean eventHandle(MouseEvent e) {
		if (rect.contains(e.getPoint())) {
			if ("toggle".equals(type)) {
				value = !(boolean) value;
				return true;
			}
		}
		return false;
	}
}
