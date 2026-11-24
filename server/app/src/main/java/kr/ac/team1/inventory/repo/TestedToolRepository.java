package kr.ac.team1.inventory.repo;

import kr.ac.team1.inventory.domain.TestedTool;
import org.springframework.data.jpa.repository.JpaRepository;

public interface TestedToolRepository extends JpaRepository<TestedTool, String> {
}
