package com.inventory.domain;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@JsonIgnoreProperties(ignoreUnknown = true)
public class AutoMeta {
    public long stars;
    public String pushed_at;
    public String license;
    public int open_issues;
}
