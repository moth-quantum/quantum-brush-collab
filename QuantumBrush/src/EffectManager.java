import processing.core.*;
import processing.data.*;
import java.io.*;
import java.util.*;

public class EffectManager {
    private QuantumBrush app;
    private HashMap<String, Effect> effects;
    
    public EffectManager(QuantumBrush app) {
        this.app = app;
        this.effects = new HashMap<>();
    }
    
    public void loadEffects() {
        File effectsDir = new File("effect");
        if (!effectsDir.exists() || !effectsDir.isDirectory()) {
            System.err.println("Error: effect directory not found or not a directory");
            return;
        }
        
        File[] effectFolders = effectsDir.listFiles(File::isDirectory);
        
        if (effectFolders == null || effectFolders.length == 0) {
            System.out.println("No effect folders found in effect directory");
            return;
        }
        
        for (File folder : effectFolders) {
            String folderName = folder.getName();
            
            // Look for requirements JSON files
            File[] jsonFiles = folder.listFiles(
                (dir, name) -> name.toLowerCase().endsWith("_requirements.json")
            );
            
            if (jsonFiles != null && jsonFiles.length > 0) {
                for (File jsonFile : jsonFiles) {
                    try {
                        JSONObject requirements = app.loadJSONObject(jsonFile.getAbsolutePath());
                        
                        // Get the effect ID from the JSON file
                        String effectId = requirements.getString("id", folderName);
                        
                        // Create an Effect object
                        Effect effect = new Effect(effectId, folderName, requirements);
                        
                        // Store the effect using its ID as the key
                        effects.put(effectId, effect);
                        
                        System.out.println(
                            "Loaded effect: " + effectId + " from folder: " + folderName
                        );
                    } catch (Exception e) {
                        System.err.println(
                            "Error loading effect from " + jsonFile.getName() + 
                            ": " + e.getMessage()
                        );
                    }
                }
            } else {
                System.out.println("No requirements JSON files found in folder: " + folderName);
            }
        }
    }
    
    public Effect getEffect(String id) {
        return effects.get(id);
    }
    
    public Set<String> getEffectNames() {
        return effects.keySet();
    }
}

class Effect {
    private String id;
    private String folderName;
    private JSONObject requirements;
    
    public Effect(String id, String folderName, JSONObject requirements) {
        this.id = id;
        this.folderName = folderName;
        this.requirements = requirements;
    }
    
    public String getId() {
        return id;
    }
    
    public String getFolderName() {
        return folderName;
    }
    
    public String getName() {
        // Return the display name from requirements, or fall back to ID
        return requirements.getString("name", id);
    }
    
    public JSONObject getRequirements() {
        return requirements;
    }
    
    public JSONObject getUserInputRequirements() {
        if (requirements.hasKey("user_input")) {
            return requirements.getJSONObject("user_input");
        }
        return new JSONObject();
    }
    
    public Map<String, Object> getDefaultParameters() {
        Map<String, Object> params = new HashMap<>();
        JSONObject userInput = getUserInputRequirements();
        
        for (Object key : userInput.keys()) {
            String paramName = (String) key;
            Object defaultValue = userInput.get(paramName);
            params.put(paramName, defaultValue);
        }
        
        return params;
    }
}
