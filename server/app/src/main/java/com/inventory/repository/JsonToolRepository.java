package com.inventory.repository;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.inventory.domain.Tool;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Repository;

import java.io.File;
import java.util.*;

@Repository
public class JsonToolRepository implements ToolRepository {

    @Value("${inventory.data-dir:../sample-data}")
    private String dataDir;

    private List<Tool> tools = new ArrayList<>();

    @PostConstruct
    public void load() throws Exception {
        ObjectMapper mapper = new ObjectMapper();
        File file = new File(dataDir, "entries.json");
        JsonNode root = mapper.readTree(file);
        JsonNode entries = root.get("entries");
        for (JsonNode node : entries) {
            tools.add(mapper.treeToValue(node, Tool.class));
        }
    }

    @Override
    public List<Tool> findAll() {
        return Collections.unmodifiableList(tools);
    }

    @Override
    public Optional<Tool> findById(String id) {
        return tools.stream().filter(t -> t.id.equals(id)).findFirst();
    }

    @Override
    public List<Tool> findByCategory(int category) {
        return tools.stream().filter(t -> t.category == category).toList();
    }
}
