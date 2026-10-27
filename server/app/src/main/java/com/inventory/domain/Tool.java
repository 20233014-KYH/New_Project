package com.inventory.domain;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public class Tool {
    public String id;
    public String repo;
    public List<String> aliases;
    public String name;
    public int category;
    public String summary_ko;
    public String role_summary;
    public String install_basis;
    public String version;
    public String checked_at;
    public Scope scope;
    public long always_on_tokens_est;
    public Object token_effect;
    public String token_note;
    public String install;
    public Object cautions;
    public List<Object> reviews;
    public AutoMeta auto;
}
