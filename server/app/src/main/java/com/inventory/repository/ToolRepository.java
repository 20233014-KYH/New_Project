package com.inventory.repository;

import com.inventory.domain.Tool;
import java.util.List;
import java.util.Optional;

public interface ToolRepository {
    List<Tool> findAll();
    Optional<Tool> findById(String id);
    List<Tool> findByCategory(int category);
}
