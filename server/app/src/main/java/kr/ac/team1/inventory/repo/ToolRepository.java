package kr.ac.team1.inventory.repo;

import kr.ac.team1.inventory.domain.Tool;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ToolRepository extends JpaRepository<Tool, String> {
}
