package com.inventory.domain;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public class Judgment {
    public String a;
    public String b;
    public String relation;
    public String reason_ko;
    public List<Evidence> evidence;
    public String a_version;
    public String b_version;
    public String judged_at;
    public String criteria_version;
    public String review_state;
    public boolean needs_review;
}
