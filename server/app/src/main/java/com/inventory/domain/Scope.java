package com.inventory.domain;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.Map;

@JsonIgnoreProperties(ignoreUnknown = true)
public class Scope {
    public int skills;
    public int agents;
    public int commands;
    public int mcp;
    public int hooks_total;
    public Map<String, Integer> hook_events;
}
