import processing.core.*;
import processing.data.*;
import java.io.*;
import java.util.*;
import java.nio.file.*;
import javax.swing.*;

public class FileManager {
    private QuantumBrush app;
    
    public FileManager(QuantumBrush app) {
        this.app = app;
        
        // Create project directory if it doesn't exist
        ensureDirectoryExists("project");
    }
    
    public void saveProject(String projectId, PImage originalImage) {
        String projectPath = "project/" + projectId;
        ensureDirectoryExists(projectPath);
        
        // Save original image
        if (originalImage != null) {
            originalImage.save(projectPath + "/original.png");
        }
    }
    
    public boolean ensureDirectoryExists(String path) {
        File directory = new File(path);
        if (!directory.exists()) {
            return directory.mkdirs();
        }
        return true;
    }

    public void saveStroke(
        String projectId, 
        String strokeId, 
        JSONObject instructions, 
        PImage inputImage
    ) {
        String strokeDirPath = "project/" + projectId + "/stroke";
        ensureDirectoryExists(strokeDirPath);
        
        // Save instructions
        String instructionsPath = strokeDirPath + "/" + strokeId + "_instructions.json";
        app.saveJSONObject(instructions, instructionsPath);
        
        // Save input image
        if (inputImage != null) {
            String imagePath = strokeDirPath + "/" + strokeId + "_input.png";
            inputImage.save(imagePath);
        }
    }
    
    public JSONObject loadEffectRequirements(String effectName) {
        File requirementsFile = new File(
            "effect/" + effectName + "/" + effectName + "_requirements.json"
        );
        if (requirementsFile.exists()) {
            try {
                return app.loadJSONObject(requirementsFile.getAbsolutePath());
            } catch (Exception e) {
                System.err.println("Error loading effect requirements: " + e.getMessage());
            }
        }
        return null;
    }

    public void createProjectMetadata(String projectId, String projectName) {
        // Create metadata directory if it doesn't exist
        ensureDirectoryExists("metadata");
        
        // Create metadata JSON
        JSONObject metadata = new JSONObject();
        metadata.setString("project_name", projectName);
        metadata.setString("project_id", projectId);
        
        // Set timestamps
        long currentTime = System.currentTimeMillis();
        metadata.setLong("created_time", currentTime);
        metadata.setLong("modified_time", currentTime);
        
        // Save metadata
        app.saveJSONObject(metadata, "metadata/" + projectId + ".json");
    }

    public void updateProjectMetadata(String projectId) {
        String metadataPath = "metadata/" + projectId + ".json";
        File metadataFile = new File(metadataPath);
        
        if (metadataFile.exists()) {
            try {
                JSONObject metadata = app.loadJSONObject(metadataPath);
                metadata.setLong("modified_time", System.currentTimeMillis());
                app.saveJSONObject(metadata, metadataPath);
            } catch (Exception e) {
                System.err.println("Error updating metadata: " + e.getMessage());
            }
        }
    }

    public ArrayList<JSONObject> getProjectsMetadata() {
        ArrayList<JSONObject> projects = new ArrayList<>();
        
        File metadataDir = new File("metadata");
        if (!metadataDir.exists()) {
            ensureDirectoryExists("metadata");
            return projects;
        }
        
        File[] metadataFiles = metadataDir.listFiles(
            (dir, name) -> name.toLowerCase().endsWith(".json")
        );
        
        if (metadataFiles != null) {
            for (File file : metadataFiles) {
                try {
                    // Check if the corresponding project directory exists
                    JSONObject metadata = app.loadJSONObject(file.getAbsolutePath());
                    String projectId = metadata.getString("project_id", "");
                    File projectDir = new File("project/" + projectId);
                    
                    // Only add to the list if the project directory exists
                    if (projectDir.exists() && projectDir.isDirectory()) {
                        projects.add(metadata);
                    } else {
                        // If project directory doesn't exist, delete the orphaned metadata file
                        System.out.println("Removing orphaned metadata for project: " + projectId);
                        file.delete();
                    }
                } catch (Exception e) {
                    System.err.println(
                        "Error loading metadata from " + file.getName() + 
                        ": " + e.getMessage()
                    );
                }
            }
        }
        
        // Sort by modified time (most recent first)
        projects.sort(
            (a, b) -> Long.compare(
                b.getLong("modified_time", 0), 
                a.getLong("modified_time", 0)
            )
        );
        
        return projects;
    }

    public JSONObject getProjectMetadata(String projectId) {
        String metadataPath = "metadata/" + projectId + ".json";
        File metadataFile = new File(metadataPath);
        
        if (metadataFile.exists()) {
            try {
                return app.loadJSONObject(metadataPath);
            } catch (Exception e) {
                System.err.println("Error loading metadata: " + e.getMessage());
            }
        }
        
        return null;
    }

    // Add a method to load strokes when a project is loaded
    public boolean loadProject(String projectId) {
        String projectPath = "project/" + projectId;
        File projectDir = new File(projectPath);
        
        if (!projectDir.exists()) {
            return false;
        }
        
        // Load original image
        File originalImageFile = new File(projectPath + "/original.png");
        if (originalImageFile.exists()) {
            PImage loadedImage = app.loadImage(originalImageFile.getAbsolutePath());
            if (loadedImage != null) {
                app.setCurrentImage(loadedImage);
            
                // Resize window to match image size
                app.getSurface().setSize(loadedImage.width, loadedImage.height);
            
                // Update metadata
                updateProjectMetadata(projectId);
            
                // Load existing strokes for this project
                app.getStrokeManager().loadExistingStrokes();
            
                return true;
            }
        }
    
        return false;
    }

    public String formatTimestamp(long timestamp) {
        java.text.SimpleDateFormat sdf = new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        return sdf.format(new java.util.Date(timestamp));
    }
    
    /**
     * Deletes a project and all its associated files and metadata.
     * 
     * @param projectId The ID of the project to delete
     * @return true if the project was successfully deleted, false otherwise
     */
    public boolean deleteProject(String projectId) {
        if (projectId == null || projectId.isEmpty()) {
            return false;
        }
        
        boolean success = true;
        
        try {
            // Delete project directory and all its contents
            File projectDir = new File("project/" + projectId);
            if (projectDir.exists()) {
                success &= deleteDirectory(projectDir);
            }
            
            // Delete metadata file
            File metadataFile = new File("metadata/" + projectId + ".json");
            if (metadataFile.exists()) {
                success &= metadataFile.delete();
            }
            
            return success;
        } catch (Exception e) {
            System.err.println("Error deleting project: " + e.getMessage());
            e.printStackTrace();
            return false;
        }
    }
    
    /**
     * Recursively deletes a directory and all its contents.
     * 
     * @param directory The directory to delete
     * @return true if the directory was successfully deleted, false otherwise
     */
    private boolean deleteDirectory(File directory) {
        if (directory.exists()) {
            File[] files = directory.listFiles();
            if (files != null) {
                for (File file : files) {
                    if (file.isDirectory()) {
                        deleteDirectory(file);
                    } else {
                        file.delete();
                    }
                }
            }
        }
        return directory.delete();
    }
}