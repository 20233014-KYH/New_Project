package com.inventory.domain;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@JsonIgnoreProperties(ignoreUnknown = true)
public class TestedInfo {
    public String tool;
    public String effect;
    public String caution;
    public String caution_work;
    public String caution_shell;
    public String date;
}
