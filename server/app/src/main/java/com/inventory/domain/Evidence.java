package com.inventory.domain;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@JsonIgnoreProperties(ignoreUnknown = true)
public class Evidence {
    public String claim;
    public String type;
    public String source;
    public String checked_at;
}
