package com.inventory.repository;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.inventory.domain.TestedInfo;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Repository;

import java.io.File;
import java.util.*;

@Repository
public class TestedRepository {

    @Value("${inventory.data-dir:../sample-data}")
    private String dataDir;

    private final Map<String, TestedInfo> byTool = new HashMap<>();

    @PostConstruct
    public void load() throws Exception {
        ObjectMapper mapper = new ObjectMapper();
        File file = new File(dataDir, "tested.json");
        JsonNode root = mapper.readTree(file);
        JsonNode arr = root.get("tested");
        for (JsonNode node : arr) {
            TestedInfo t = mapper.treeToValue(node, TestedInfo.class);
            byTool.put(t.tool, t);
        }
    }

    public Optional<TestedInfo> findByTool(String toolId) {
        return Optional.ofNullable(byTool.get(toolId));
    }

    public Collection<TestedInfo> findAll() {
        return byTool.values();
    }
}
